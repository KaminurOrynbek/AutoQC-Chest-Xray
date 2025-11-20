from app.repositories.exam_repository import ExamRepository
from app.models.exams import Exam
from sqlmodel import Session
from typing import List, Optional

class ExamService:
    def __init__(self, session: Session):
        self.repo = ExamRepository(session)

    def create_exam(self, exam: Exam) -> Exam:
        return self.repo.create(exam)

    def get_exam(self, exam_id: int) -> Optional[Exam]:
        return self.repo.get(exam_id)

    def list_exams(self, patient_id: Optional[int] = None, date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Exam]:
        return self.repo.list(patient_id, date_from, date_to)
