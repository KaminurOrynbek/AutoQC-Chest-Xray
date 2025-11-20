from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional
from .patients import Patient

class Exam(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: str = Field(foreign_key="patient.patient_id")  # <-- строка, FK на patient.patient_id
    accession_number: str = Field(sa_column_kwargs={"unique": True, "nullable": False})
    exam_date: datetime
    modality: str
    view_type: str
    device: str
    technician: str
    notes: Optional[str] = None

    patient: Optional[Patient] = Relationship()
