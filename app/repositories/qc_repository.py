from sqlmodel import Session, select
from app.models.qc_records import QCRecord
from typing import List, Optional

class QCRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, qc_record: QCRecord) -> QCRecord:
        self.session.add(qc_record)
        self.session.commit()
        self.session.refresh(qc_record)
        return qc_record

    def get_by_exam(self, exam_id: int) -> List[QCRecord]:
        query = select(QCRecord).where(QCRecord.exam_id == exam_id)
        return self.session.exec(query).all()

    def list(self, patient_id: Optional[int] = None, date_from: Optional[str] = None, date_to: Optional[str] = None, flag: Optional[str] = None) -> List[QCRecord]:
        query = select(QCRecord)
        if patient_id:
            query = query.join(QCRecord.exam).where(QCRecord.exam.patient_id == patient_id)
        if date_from:
            query = query.where(QCRecord.created_at >= date_from)
        if date_to:
            query = query.where(QCRecord.created_at <= date_to)
        if flag:
            query = query.where(QCRecord.ml_results_json.contains(flag))
        return self.session.exec(query).all()
