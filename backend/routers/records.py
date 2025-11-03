from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from typing import List
from backend.db import get_session
from backend.models import ScanRecord, QCFinding, Report

router = APIRouter()


# ---- Pydantic-compatible схемы для сериализации ----
class ScanRecordRead(ScanRecord):
    class Config:
        orm_mode = True  # позволяет сериализовать ORM объекты


# ---- Эндпоинт ----
@router.get("/records/", response_model=List[ScanRecordRead])
def get_records(session: Session = Depends(get_session)):
    records = session.exec(select(ScanRecord)).all()
    return records
