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
from reportlab.lib.utils import ImageReader
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
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

            # --- сохраняем оригинал ---
            original_b64 = ml_result.get("original_image_base64") or ml_result.get("original")
            if original_b64:
                original_bytes = base64.b64decode(original_b64)
                original_dir = os.path.join("app", "uploads", "original")
                os.makedirs(original_dir, exist_ok=True)
                original_path = os.path.join(original_dir, f"{qc_record.id}.png")
                with open(original_path, "wb") as f:
                    f.write(original_bytes)
                qc_record.original_image_path = original_path

            # --- сохраняем исправленное изображение ---
            corrected_b64 = ml_result.get("processed_image_base64") or ml_result.get("corrected_image_base64") or ml_result.get("processed")
            if corrected_b64:
                corrected_bytes = base64.b64decode(corrected_b64)
                corrected_dir = os.path.join("app", "uploads", "corrected")
                os.makedirs(corrected_dir, exist_ok=True)
                corrected_path = os.path.join(corrected_dir, f"{qc_record.id}.png")
                with open(corrected_path, "wb") as f:
                    f.write(corrected_bytes)
                qc_record.corrected_image_path = corrected_path

            # update ml_results_json may remain as-is
            session.add(qc_record)
            session.commit()
            session.refresh(qc_record)
            return qc_record
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
            # Prefer serving stored file paths if available
            if original and record.original_image_path and os.path.isfile(record.original_image_path):
                return StreamingResponse(open(record.original_image_path, "rb"), media_type="image/png")
            if not original and record.corrected_image_path and os.path.isfile(record.corrected_image_path):
                return StreamingResponse(open(record.corrected_image_path, "rb"), media_type="image/png")

            # Fallback to ML JSON base64 content
            ml_results = json.loads(record.ml_results_json or "{}")
            key = "original_image_base64" if original else "processed_image_base64"
            img_b64 = ml_results.get(key)
            if not img_b64:
                # try alternative keys
                if original:
                    img_b64 = ml_results.get("original")
                else:
                    img_b64 = ml_results.get("processed")

            if not img_b64:
                raise RuntimeError("Image not found")

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

            # Patient information block
            try:
                c.setFont(font_bold_name, 12)
                c.drawString(margin, y, "Информация о пациенте / Пациент туралы ақпарат")
                y -= 14
                c.setFont(font_name, 10)
                if patient:
                    first = getattr(patient, 'first_name', '') or ''
                    last = getattr(patient, 'last_name', '') or ''
                    patient_identifier = getattr(patient, 'patient_id', '') or ''
                    birth = getattr(patient, 'birth_date', None)
                    sex = getattr(patient, 'sex', '') or ''
                    # compute age at exam date if possible
                    age_str = ''
                    try:
                        if birth and getattr(exam, 'exam_date', None):
                            age = (exam.exam_date.date() - birth).days / 365.25
                            age_str = f"{int(age)}"
                    except Exception:
                        age_str = ''

                    c.drawString(margin, y, f"Имя / Аты: {first} {last}    (ID: {patient_identifier})")
                    y -= 12
                    if birth:
                        c.drawString(margin, y, f"Дата рождения / Туған күні: {birth}    Возраст на момент исследования: {age_str}")
                        y -= 12
                    else:
                        c.drawString(margin, y, f"Дата рождения / Туған күні: —")
                        y -= 12
                    c.drawString(margin, y, f"Пол / Жынысы: {sex}")
                    y -= 14
                else:
                    c.drawString(margin, y, "Пациент: информация не найдена")
                    y -= 14
            except Exception:
                # if anything fails, continue silently
                pass

            # Small function to draw a matplotlib figure into the PDF
            def draw_fig(fig, x, y_pos, max_w, max_h):
                img_buf = io.BytesIO()
                fig.savefig(img_buf, bbox_inches='tight', dpi=150)
                plt.close(fig)
                img_buf.seek(0)
                img = ImageReader(img_buf)
                iw, ih = img.getSize()
                # scale to fit
                scale = min(max_w / iw, max_h / ih, 1.0)
                render_w = iw * scale
                render_h = ih * scale
                c.drawImage(img, x, y_pos - render_h, width=render_w, height=render_h)
                return render_h

            # Generate small charts: exams per day (top 10), modality distribution, heatmap
            try:
                # exams per day
                days_items = sorted(counts_by_day.items())
                if days_items:
                    dates, counts = zip(*days_items)
                    fig = plt.figure(figsize=(6, 2))
                    plt.bar(dates[-20:], counts[-20:])
                    plt.xticks(rotation=45, fontsize=6)
                    plt.title('Exams per day')
                    h = draw_fig(fig, margin, y, width - 2*margin, 120)
                    y -= (h + 8)

                # modality pie
                if modality_counts:
                    labels = list(modality_counts.keys())[:8]
                    sizes = [modality_counts[k] for k in labels]
                    fig = plt.figure(figsize=(4, 3))
                    plt.pie(sizes, labels=labels, autopct='%1.1f%%')
                    plt.title('Modality distribution')
                    h = draw_fig(fig, margin, y, width/2 - margin, 150)
                    # move x to the right for next chart
                    right_x = margin + (width/2)
                    # heatmap
                    heat = [[heatmap.get((dow, hr), 0) for hr in range(24)] for dow in range(7)]
                    fig2 = plt.figure(figsize=(4, 3))
                    plt.imshow(heat, aspect='auto', cmap='hot')
                    plt.title('Heatmap (weekday x hour)')
                    plt.xlabel('Hour')
                    plt.ylabel('Weekday')
                    h2 = draw_fig(fig2, right_x, y, width/2 - margin, 150)
                    y -= (max(h, h2) + 8)
            except Exception:
                # If plotting fails, continue without charts
                pass

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

            # Include QC records history for this exam (simple table)
            try:
                qc_history = session.query(QCModel).filter(QCModel.exam_id == exam_id).order_by(QCModel.created_at).all()
                if qc_history:
                    if y < margin + 120:
                        c.showPage(); y = height - margin
                    c.setFont(font_bold_name, 11)
                    c.drawString(margin, y, "История QC / QC тарихы")
                    y -= 14
                    c.setFont(font_name, 9)
                    for q in qc_history:
                        ml = json.loads(q.ml_results_json or '{}')
                        status = ml.get('status') or ml.get('qc_status') or ('FIXED' if q.corrected_image_path else 'FLAGGED')
                        probs = ml.get('qc_probs') or {}
                        created_by = getattr(q, 'created_by', '')
                        created_at = getattr(q, 'created_at', '')
                        line = f"{created_at} | by: {created_by} | status: {status} | probs: {', '.join([f'{k}:{v:.2f}' for k,v in (probs.items() if isinstance(probs, dict) else [])][:3])}"
                        c.drawString(margin, y, line)
                        y -= 10
                        # include thumbnails (original / corrected) if available
                        thumb_h = 0
                        if q.original_image_path and os.path.isfile(q.original_image_path):
                            try:
                                img = ImageReader(q.original_image_path)
                                iw, ih = img.getSize()
                                scale = min((80) / iw, (60) / ih, 1.0)
                                c.drawImage(img, margin, y - 60, width=iw*scale, height=ih*scale)
                                thumb_h = max(thumb_h, ih*scale)
                            except Exception:
                                pass
                        if q.corrected_image_path and os.path.isfile(q.corrected_image_path):
                            try:
                                img2 = ImageReader(q.corrected_image_path)
                                iw2, ih2 = img2.getSize()
                                scale2 = min((80) / iw2, (60) / ih2, 1.0)
                                c.drawImage(img2, margin + 90, y - 60, width=iw2*scale2, height=ih2*scale2)
                                thumb_h = max(thumb_h, ih2*scale2)
                            except Exception:
                                pass
                        if thumb_h:
                            y -= (thumb_h + 8)
                        if y < margin + 80:
                            c.showPage(); y = height - margin
            except Exception:
                pass

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

            # Embed original/corrected images for the current exam (if present)
            try:
                exam_qc_latest = exam_qc[-1] if exam_qc else None
                if exam_qc_latest:
                    img_x = margin
                    img_max_w = (width - 2*margin) / 2 - 8
                    img_max_h = 160
                    # original
                    if exam_qc_latest.original_image_path and os.path.isfile(exam_qc_latest.original_image_path):
                        img = ImageReader(exam_qc_latest.original_image_path)
                        iw, ih = img.getSize()
                        scale = min(img_max_w/iw, img_max_h/ih, 1.0)
                        c.drawImage(img, img_x, y - ih*scale, width=iw*scale, height=ih*scale)
                    # corrected
                    if exam_qc_latest.corrected_image_path and os.path.isfile(exam_qc_latest.corrected_image_path):
                        img2 = ImageReader(exam_qc_latest.corrected_image_path)
                        iw2, ih2 = img2.getSize()
                        scale2 = min(img_max_w/iw2, img_max_h/ih2, 1.0)
                        c.drawImage(img2, img_x + img_max_w + 16, y - ih2*scale2, width=iw2*scale2, height=ih2*scale2)
                    y -= (img_max_h + 12)
            except Exception:
                pass

            c.showPage()
            c.save()

            buf.seek(0)
            return StreamingResponse(buf, media_type='application/pdf')
        finally:
            session.close()
