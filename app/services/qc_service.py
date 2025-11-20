import json
import base64
import io
from PIL import Image
import requests
from fastapi import UploadFile
from fastapi.responses import StreamingResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import statistics

from app.models.qc_records import QCRecord
from app.config.db import get_session

ML_URL = "http://localhost:8001/qc/preprocess"


class QCService:
    @staticmethod
    def pil_to_base64(img: Image.Image) -> str:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def upload_qc(self, exam_id: int, file: UploadFile, user_id: int):
        if not file:
            raise RuntimeError("Файл не передан")

        # --- отправка в ML сервис ---
        try:
            files = {"file": (file.filename, file.file, file.content_type)}
            response = requests.post(ML_URL, files=files)
            response.raise_for_status()
            ml_result = response.json()
        except Exception as e:
            raise RuntimeError(f"Ошибка при работе с ML сервисом: {e}")

        session = next(get_session())
        try:
            qc_record = QCRecord(
                exam_id=exam_id,
                original_image_path="",
                corrected_image_path="",
                ml_results_json=json.dumps(ml_result),
                created_by=user_id,
            )
            session.add(qc_record)
            session.commit()
            session.refresh(qc_record)
            return qc_record  # всегда возвращаем ORM-объект
        finally:
            session.close()

    def get_qc_by_exam(self, exam_id: int):
        session = next(get_session())
        try:
            record = session.query(QCRecord).filter(QCRecord.exam_id == exam_id).first()
            return record
        finally:
            session.close()

    def list_qc(self, patient_id: str = None, date_from: str = None, date_to: str = None, flag: str = None):
        session = next(get_session())
        try:
            query = session.query(QCRecord)
            if patient_id:
                query = query.join(QCRecord.exam).filter_by(patient_id=patient_id)
            return query.all()
        finally:
            session.close()

    def get_image_response(self, qc_id: int, original: bool = True):
        session = next(get_session())
        try:
            record = session.query(QCRecord).filter(QCRecord.id == qc_id).first()
            if not record:
                raise RuntimeError("QC record not found")

            ml_results = json.loads(record.ml_results_json)
            key = "original_image_base64" if original else "processed_image_base64"
            img_b64 = ml_results.get(key)
            if not img_b64:
                raise RuntimeError("Image not found in ML results")

            img_bytes = base64.b64decode(img_b64)
            return StreamingResponse(io.BytesIO(img_bytes), media_type="image/png")
        finally:
            session.close()

    def generate_report_pdf(self, exam_id: int):
        """Generate a bilingual (RU/KK) PDF report for the given exam_id.

        This implementation gathers basic global stats and exam-specific data
        and lays out a simple text report. It is intentionally lightweight.

        Returns: StreamingResponse (application/pdf)
        """
        session = next(get_session())
        try:
            # Gather exam and patient info
            exam = session.query(__import__('app.models.exams', fromlist=['Exam']).Exam).filter_by(id=exam_id).first()
            if not exam:
                raise RuntimeError("Exam not found")

            patient = None
            try:
                Patient = __import__('app.models.patients', fromlist=['Patient']).Patient
                patient = session.query(Patient).filter_by(patient_id=exam.patient_id).first()
            except Exception:
                patient = None

            # Global stats (Exams + Patients)
            ExamModel = __import__('app.models.exams', fromlist=['Exam']).Exam
            PatientModel = __import__('app.models.patients', fromlist=['Patient']).Patient
            all_exams = session.query(ExamModel).all()
            all_patients = session.query(PatientModel).all()

            total_exams = len(all_exams)
            total_patients = len(all_patients)

            # Counts by day/week/month
            days = [e.exam_date.date() for e in all_exams if getattr(e, 'exam_date', None)]
            counts_by_day = Counter(days)
            weeks = [e.exam_date.isocalendar()[1] for e in all_exams if getattr(e, 'exam_date', None)]
            counts_by_week = Counter(weeks)
            months = [(e.exam_date.year, e.exam_date.month) for e in all_exams if getattr(e, 'exam_date', None)]
            counts_by_month = Counter(months)

            # Heatmap hours x weekday
            heatmap = defaultdict(int)
            for e in all_exams:
                if not getattr(e, 'exam_date', None):
                    continue
                dt = e.exam_date
                heatmap[(dt.weekday(), dt.hour)] += 1

            # Average age at exam
            ages = []
            for e in all_exams:
                try:
                    p = session.query(PatientModel).filter_by(patient_id=e.patient_id).first()
                    if p and getattr(p, 'birth_date', None) and getattr(e, 'exam_date', None):
                        age = (e.exam_date.date() - p.birth_date).days / 365.25
                        ages.append(age)
                except Exception:
                    continue
            avg_age = statistics.mean(ages) if ages else None

            # Distributions
            modality_counts = Counter([e.modality for e in all_exams if getattr(e, 'modality', None)])
            view_counts = Counter([e.view_type for e in all_exams if getattr(e, 'view_type', None)])
            device_counts = Counter([e.device for e in all_exams if getattr(e, 'device', None)])

            avg_exams_per_patient = (total_exams / total_patients) if total_patients else 0

            # Frequent patients ( >3 exams in last 365 days )
            one_year_ago = datetime.utcnow() - timedelta(days=365)
            recent_exams = [e for e in all_exams if getattr(e, 'exam_date', None) and e.exam_date >= one_year_ago]
            patient_exam_count = Counter([e.patient_id for e in recent_exams])
            frequent_patients = sum(1 for c in patient_exam_count.values() if c > 3)
            frequent_patients_share = (frequent_patients / total_patients) if total_patients else 0

            # QC corrections metrics (global and for this exam)
            QCModel = __import__('app.models.qc_records', fromlist=['QCRecord']).QCRecord
            all_qc = session.query(QCModel).all()
            total_qc = len(all_qc)
            corrected_qc = [q for q in all_qc if getattr(q, 'corrected_image_path', None)]
            corrected_percent = (len(corrected_qc) / total_qc * 100) if total_qc else 0

            exam_qc = session.query(QCModel).filter(QCModel.exam_id == exam_id).all()
            exam_total_qc = len(exam_qc)
            exam_corrected = [q for q in exam_qc if getattr(q, 'corrected_image_path', None)]
            exam_corrected_percent = (len(exam_corrected) / exam_total_qc * 100) if exam_total_qc else 0

            # Optional comparison before/after for a chosen metric (e.g., lung_coverage_low)
            def extract_prob(record, key='lung_coverage_low'):
                try:
                    data = json.loads(record.ml_results_json or '{}')
                    # try multiple common locations
                    qc_probs = data.get('qc_probs') or data.get('probs') or {}
                    if isinstance(qc_probs, dict) and key in qc_probs:
                        return float(qc_probs[key])
                except Exception:
                    return None
                return None

            before_vals = [extract_prob(q) for q in exam_qc]
            before_vals = [v for v in before_vals if v is not None]
            avg_before = statistics.mean(before_vals) if before_vals else None

            # If after-probs exist under 'post_fix_qc_probs' or 'corrected_qc_probs'
            def extract_after_prob(record, key='lung_coverage_low'):
                try:
                    data = json.loads(record.ml_results_json or '{}')
                    after = data.get('post_fix_qc_probs') or data.get('corrected_qc_probs') or {}
                    if isinstance(after, dict) and key in after:
                        return float(after[key])
                except Exception:
                    return None
                return None

            after_vals = [extract_after_prob(q) for q in exam_qc]
            after_vals = [v for v in after_vals if v is not None]
            avg_after = statistics.mean(after_vals) if after_vals else None

            # Register a TTF font that supports Cyrillic (RU/KK). Try common system fonts.
            font_name = None
            font_bold_name = None
            candidates = [
                # common cross-platform
                ("DejaVuSans", "DejaVuSans-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
                # Windows common fonts
                ("Arial", "Arial-Bold", os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'arial.ttf'), os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'arialbd.ttf')),
                ("Tahoma", "Tahoma-Bold", os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'tahoma.ttf'), os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'tahomabd.ttf')),
                ("Verdana", "Verdana-Bold", os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'verdana.ttf'), os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'verdanab.ttf')),
            ]

            for base_name, bold_name, path_regular, path_bold in candidates:
                try:
                    if os.path.isfile(path_regular):
                        pdfmetrics.registerFont(TTFont(base_name, path_regular))
                        font_name = base_name
                        if os.path.isfile(path_bold):
                            pdfmetrics.registerFont(TTFont(bold_name, path_bold))
                            font_bold_name = bold_name
                        else:
                            font_bold_name = font_name
                        break
                except Exception:
                    continue

            # Fallback to built-in fonts if nothing found (may not support Cyrillic)
            if not font_name:
                font_name = 'Helvetica'
                font_bold_name = 'Helvetica-Bold'

            # Build PDF
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=A4)
            width, height = A4

            margin = 2 * cm
            y = height - margin

            def write_line_ru_kk(ru: str, kk: str, y_pos: float, size=10):
                c.setFont(font_bold_name, size)
                c.drawString(margin, y_pos, ru)
                c.setFont(font_name, size)
                c.drawString(width/2, y_pos, kk)

            # Header
            c.setFont(font_bold_name, 14)
            c.drawString(margin, y, "Отчёт QC / QC есеп (RU / KK)")
            y -= 20

            # Exam / patient summary
            c.setFont(font_bold_name, 12)
            c.drawString(margin, y, "1. Общая активность и нагрузка / Жалпылама белсенділік және жүктеме")
            y -= 16

            c.setFont(font_name, 10)
            c.drawString(margin, y, f"Всего исследований: {total_exams} | Барлық зерттеулер: {total_exams}")
            y -= 12
            c.drawString(margin, y, f"Всего пациентов: {total_patients} | Барлық пациенттер: {total_patients}")
            y -= 12
            if avg_age:
                c.drawString(margin, y, f"Средний возраст пациентов: {avg_age:.1f} лет | Пациенттердің орташа жасы: {avg_age:.1f}")
                y -= 12

            c.drawString(margin, y, f"Среднее исследований на пациента: {avg_exams_per_patient:.2f}")
            y -= 14

            # Modality / view / device
            c.setFont(font_bold_name, 11)
            c.drawString(margin, y, "По типам исследований / Зерттеу түрлері")
            y -= 12
            c.setFont(font_name, 10)
            for k, v in modality_counts.most_common(10):
                c.drawString(margin, y, f"{k}: {v}")
                y -= 10
                if y < margin + 50:
                    c.showPage()
                    y = height - margin

            # Corrections
            if y < margin + 60:
                c.showPage()
                y = height - margin

            c.setFont(font_bold_name, 12)
            c.drawString(margin, y, "2. Аналитика по исправлениям / Түзетулерге талдау")
            y -= 14
            c.setFont(font_name, 10)
            c.drawString(margin, y, f"Всего QC записей: {total_qc}")
            y -= 12
            c.drawString(margin, y, f"% исправленных (глобально): {corrected_percent:.1f}%")
            y -= 12
            c.drawString(margin, y, f"% исправленных для этого исследования: {exam_corrected_percent:.1f}%")
            y -= 12

            if avg_before is not None:
                c.drawString(margin, y, f"Пример сравнения (lung_coverage_low) до: {avg_before:.3f}")
                y -= 12
            if avg_after is not None:
                c.drawString(margin, y, f"после: {avg_after:.3f}")
                y -= 12

            # Footer with exam info
            if y < margin + 50:
                c.showPage()
                y = height - margin

            c.setFont(font_bold_name, 11)
            c.drawString(margin, y, "Исследование / Зерттеу")
            y -= 12
            c.setFont(font_name, 10)
            c.drawString(margin, y, f"Exam ID: {exam.id}  | Accession: {getattr(exam, 'accession_number', '')}")
            y -= 12
            if patient:
                c.drawString(margin, y, f"Пациент: {getattr(patient, 'first_name', '')} {getattr(patient, 'last_name', '')} ({getattr(patient, 'patient_id', '')})")
                y -= 12

            c.showPage()
            c.save()

            buf.seek(0)
            return StreamingResponse(buf, media_type='application/pdf')
        finally:
            session.close()
