import json
import base64
import io
from PIL import Image
import requests
from fastapi import UploadFile
from fastapi.responses import StreamingResponse

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
