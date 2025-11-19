from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List
from .patients import Patient

class Exam(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="patient.id")
    accession_number: str = Field(sa_column_kwargs={"unique": True, "nullable": False})
    exam_date: datetime
    modality: str
    view_type: str
    device: str
    technician: str
    notes: Optional[str] = None

    patient: Optional[Patient] = Relationship()
