from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlmodel import Session, select
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from backend.db import engine
from backend.models import ScanRecord, QCFinding, Report
from backend.auth import get_current_user

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")

router = APIRouter(
    tags=["reports"]
)

from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from backend.auth import SECRET_KEY, ALGORITHM

security = HTTPBearer()

@router.post("/{patient_id}/generate", summary="Generate Report")
def generate_report(patient_id: str, token: str):
    try:
        # Verify the token
        payload = jwt.decode(token.replace("Bearer ", ""), SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    with Session(engine) as session:
        record = session.exec(select(ScanRecord).where(ScanRecord.patient_id == patient_id)).first()
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")

        findings = session.exec(select(QCFinding).where(QCFinding.scan_id == record.id)).all()

        filename = f"report_{patient_id}.pdf"
        filepath = os.path.join(STORAGE_DIR, filename)
        c = canvas.Canvas(filepath, pagesize=letter)
        c.setFont("Helvetica", 14)
        c.drawString(72, 720, f"CXR QC Report - {patient_id}")
        c.setFont("Helvetica", 11)
        c.drawString(72, 700, f"Date: {record.date}")
        y = 660
        for f in findings:
            c.drawString(72, y, f"{f.metric}: {f.value} - {f.status}")
            y -= 18
            if y < 72:
                c.showPage()
                y = 720
        c.save()

        report = Report(scan_id=record.id, file_path=f"/uploads/{filename}")
        session.add(report)
        session.commit()
        session.refresh(report)

        return {"report_id": report.id, "download_url": report.file_path}


@router.get("/{report_id}/download", summary="Download Report")
def download_report(report_id: int):
    with Session(engine) as session:
        report = session.get(Report, report_id)
        if not report or not report.file_path:
            raise HTTPException(status_code=404, detail="Report not found")

        file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), report.file_path.lstrip("/"))
        return FileResponse(path=file_path, filename=os.path.basename(file_path))
