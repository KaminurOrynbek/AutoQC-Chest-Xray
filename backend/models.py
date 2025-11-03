from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from pydantic import ConfigDict


class User(SQLModel, table=True):
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    full_name: Optional[str] = None
    hashed_password: str


class ScanRecord(SQLModel, table=True):
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: str = Field(index=True)
    view_type: Optional[str] = Field(default=None)
    device: Optional[str] = Field(default=None)
    qc_status: Optional[str] = Field(default="UNKNOWN")
    date: datetime = Field(default_factory=datetime.utcnow)
    image_path: Optional[str] = Field(default=None)
    report_id: Optional[int] = Field(default=None, foreign_key="report.id")


class QCFinding(SQLModel, table=True):
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    scan_id: Optional[int] = Field(default=None, foreign_key="scanrecord.id")
    metric: str
    value: str
    status: str
    recommendation: Optional[str] = Field(default=None)


class Report(SQLModel, table=True):
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    scan_id: Optional[int] = Field(default=None, foreign_key="scanrecord.id")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    file_path: Optional[str] = Field(default=None)
