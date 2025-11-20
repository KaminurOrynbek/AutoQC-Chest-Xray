from sqlmodel import Session, select
from app.models.qc_records import QCRecord
from app.models.exams import Exam
from typing import List, Optional
import json
from collections import Counter

class QCRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> List[QCRecord]:
        query = select(QCRecord)
        return self.session.exec(query).all()

    def list(
        self,
        patient_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        flag: Optional[str] = None
    ) -> List[QCRecord]:
        query = select(QCRecord)
        if patient_id:
            query = query.join(QCRecord.exam).where(Exam.patient_id == patient_id)
        if date_from:
            query = query.where(QCRecord.created_at >= date_from)
        if date_to:
            query = query.where(QCRecord.created_at <= date_to)
        if flag:
            query = query.where(QCRecord.ml_results_json.contains(flag))
        return self.session.exec(query).all()

    def summary(
        self,
        patient_id: Optional[str] = None,
    ):
        qcs = self.list(patient_id=patient_id)

        total = len(qcs)
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
