from sqlmodel import Session, select
from typing import List, Optional
from app.models.exams import Exam
from datetime import datetime

class ExamRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, exam: Exam) -> Exam:
        self.session.add(exam)
        self.session.commit()
        self.session.refresh(exam)
        return exam

    def get(self, exam_id: int) -> Optional[Exam]:
        return self.session.get(Exam, exam_id)

    def list(
        self,
        patient_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Exam]:
        query = select(Exam)
        if patient_id is not None:
            query = query.where(Exam.patient_id == patient_id)
        if date_from is not None:
            query = query.where(Exam.exam_date >= date_from)
        if date_to is not None:
            query = query.where(Exam.exam_date <= date_to)
        result = self.session.exec(query)
        return result.all()
