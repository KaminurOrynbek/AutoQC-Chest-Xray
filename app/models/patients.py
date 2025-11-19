from sqlmodel import SQLModel, Field
from datetime import date, datetime
from typing import Optional

class Patient(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: str = Field(sa_column_kwargs={"unique": True, "nullable": False})
    first_name: str
    last_name: str
    birth_date: date
    sex: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
