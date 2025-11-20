from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.config.db import get_session
from app.repositories.qc_repository import QCRepository

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary")
def dashboard_summary(session: Session = Depends(get_session)):
    repo = QCRepository(session)
    return repo.summary()

@router.get("/patient/{patient_id}")
def dashboard_patient(patient_id: str, session: Session = Depends(get_session)):
    repo = QCRepository(session)
    return repo.summary(patient_id=patient_id)

@router.get("/exam/{exam_id}")
def dashboard_exam(exam_id: int, session: Session = Depends(get_session)):
    repo = QCRepository(session)
    # просто фильтруем по exam_id
    qcs = repo.list()
    qcs = [qc for qc in qcs if qc.exam_id == exam_id]

    total = len(qcs)
    from collections import Counter
    import json

    statuses = Counter()
    major_flags = Counter()
    critical_flags = Counter()

    for qc in qcs:
        if qc.ml_results_json:
            data = json.loads(qc.ml_results_json)
            status = data.get("status", "UNKNOWN")
            statuses[status] += 1

            for k, v in data.get("major_flags", {}).items():
                if v: major_flags[k] += 1
            for k, v in data.get("critical_flags", {}).items():
                if v: critical_flags[k] += 1
        else:
            statuses["UNKNOWN"] += 1

    return {
        "total": total,
        "statuses": dict(statuses),
        "major_flags": dict(major_flags),
        "critical_flags": dict(critical_flags),
    }
