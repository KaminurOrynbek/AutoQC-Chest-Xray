from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.qc_service import QCService
import json
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/qc", tags=["QC"])

# ---------------------------
# ЗАГРУЗКА ФАЙЛА
# ---------------------------
@router.post("/{exam_id}/upload")
def upload_qc(exam_id: int, file: UploadFile = File(...), user_id: int = 1):
    service = QCService()
    try:
        qc_record = service.upload_qc(exam_id, file, user_id)
        ml_data = json.loads(qc_record.ml_results_json)

        return {
            "id": qc_record.id,
            "exam_id": qc_record.exam_id,
            "created_by": qc_record.created_by,
            "qc_probs": ml_data.get("qc_probs", {}),
            "applied_fixes": ml_data.get("applied_fixes", []),
            "severe_flags": ml_data.get("severe_flags", []),
            "needs_fix": ml_data.get("needs_fix", False),
            "original_image_url": f"/qc/{qc_record.id}/image?original=true",
            "processed_image_url": f"/qc/{qc_record.id}/image?original=false",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# ПОЛУЧЕНИЕ ПО EXAM ID
# ---------------------------
@router.get("/{exam_id}")
def get_qc_by_exam(exam_id: int):
    service = QCService()
    try:
        record = service.get_qc_by_exam(exam_id)
        if not record:
            raise HTTPException(status_code=404, detail="QC record not found")

        ml_data = json.loads(record.ml_results_json)
        return {
            "id": record.id,
            "exam_id": record.exam_id,
            "created_by": record.created_by,
            "qc_probs": ml_data.get("qc_probs", {}),
            "needs_fix": ml_data.get("needs_fix", False),
            "original_image_url": f"/qc/{record.id}/image?original=true",
            "processed_image_url": f"/qc/{record.id}/image?original=false",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# СПИСОК QC
# ---------------------------
@router.get("/")
def list_qc(patient_id: str = None, date_from: str = None, date_to: str = None, flag: str = None):
    service = QCService()
    try:
        records = service.list_qc(patient_id, date_from, date_to, flag)
        result = []
        for r in records:
            ml_data = json.loads(r.ml_results_json)
            result.append({
                "id": r.id,
                "exam_id": r.exam_id,
                "created_by": r.created_by,
                "qc_probs": ml_data.get("qc_probs", {}),
                "needs_fix": ml_data.get("needs_fix", False),
                "original_image_url": f"/qc/{r.id}/image?original=true",
                "processed_image_url": f"/qc/{r.id}/image?original=false",
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# ПОЛУЧЕНИЕ ИЗОБРАЖЕНИЙ
# ---------------------------
@router.get("/{qc_id}/image")
def get_image(qc_id: int, original: bool = True):
    service = QCService()
    try:
        return service.get_image_response(qc_id, original)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{exam_id}/report")
def get_qc_report(exam_id: int):
    """Generate bilingual PDF report (RU/KK) for given exam_id"""
    service = QCService()
    try:
        pdf_stream = service.generate_report_pdf(exam_id)
        # Add filename header
        headers = {"Content-Disposition": f"attachment; filename=qc_report_exam_{exam_id}.pdf"}
        if isinstance(pdf_stream, StreamingResponse):
            pdf_stream.headers.update(headers)
            return pdf_stream
        # otherwise wrap
        return StreamingResponse(pdf_stream, media_type='application/pdf', headers=headers)
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
