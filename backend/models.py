from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    full_name: Optional[str] = None
    hashed_password: str


class ScanRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: str = Field(index=True)
    view_type: Optional[str] = None
    device: Optional[str] = None
    qc_status: Optional[str] = "UNKNOWN"
    date: datetime = Field(default_factory=datetime.utcnow)
    image_path: Optional[str] = None
    report_id: Optional[int] = Field(default=None, foreign_key="report.id")


class QCFinding(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    scan_id: Optional[int] = Field(default=None, foreign_key="scanrecord.id")
    metric: str
    value: str
    status: str
    recommendation: Optional[str] = None


class Report(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    scan_id: Optional[int] = Field(default=None, foreign_key="scanrecord.id")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    file_path: Optional[str] = None
