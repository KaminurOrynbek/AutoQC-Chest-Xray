from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional
from .exams import Exam
from .users import User
import json

class QCRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    exam_id: int = Field(foreign_key="exam.id")
    original_image_path: str
    corrected_image_path: Optional[str] = None
    ml_results_json: Optional[str] = None  # JSON как строка
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: int = Field(foreign_key="user.id")

    exam: Optional[Exam] = Relationship()
    creator: Optional[User] = Relationship()
