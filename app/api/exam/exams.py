from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List, Optional
import json

from app.config.db import get_session
from app.services.exam_service import ExamService
from app.services.qc_service import QCService
from app.models.exams import Exam

router = APIRouter(tags=["Exams"])


@router.post("/")
def create_exam(exam: Exam, session: Session = Depends(get_session)):
    service = ExamService(session)
    exam_obj = service.create_exam(exam)

    return {
        "id": exam_obj.id,
        "patient_id": exam_obj.patient_id,
        "exam_date": exam_obj.exam_date,
        "view_type": exam_obj.view_type
    }


@router.get("/")
def list_exams(
    patient_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    session: Session = Depends(get_session)
):
    service = ExamService(session)
    exams = service.list_exams(patient_id, date_from, date_to)

    qc_service = QCService()
    result = []

    for e in exams:
        # Получаем QC record, если есть
        qc_record = qc_service.get_qc_by_exam(e.id)
        qc_summary = None
        if qc_record:
            ml_data = json.loads(qc_record.ml_results_json)
            qc_summary = {
                "qc_probs": ml_data.get("qc_probs", {}),
                "applied_fixes": ml_data.get("applied_fixes", []),
                "severe_flags": ml_data.get("severe_flags", []),
                "needs_fix": ml_data.get("needs_fix", False),
                "original_image_url": f"/qc/{qc_record.id}/image?original=true",
                "processed_image_url": f"/qc/{qc_record.id}/image?original=false"
            }

        result.append({
            "id": e.id,
            "patient_id": e.patient_id,
            "exam_date": e.exam_date,
            "view_type": e.view_type,
            "qc_summary": qc_summary
        })

    return result


@router.get("/{exam_id}")
def get_exam(exam_id: int, session: Session = Depends(get_session)):
    service = ExamService(session)
    exam = service.get_exam(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    qc_service = QCService()
    qc_record = qc_service.get_qc_by_exam(exam.id)
    qc_summary = None
    if qc_record:
        ml_data = json.loads(qc_record.ml_results_json)
        qc_summary = {
            "qc_probs": ml_data.get("qc_probs", {}),
            "applied_fixes": ml_data.get("applied_fixes", []),
            "severe_flags": ml_data.get("severe_flags", []),
            "needs_fix": ml_data.get("needs_fix", False),
            "original_image_url": f"/qc/{qc_record.id}/image?original=true",
            "processed_image_url": f"/qc/{qc_record.id}/image?original=false"
        }

    return {
        "id": exam.id,
        "patient_id": exam.patient_id,
        "exam_date": exam.exam_date,
        "view_type": exam.view_type,
        "qc_summary": qc_summary
    }
