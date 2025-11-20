import json
from typing import List, Dict, Any
from sqlmodel import Session
from app.repositories.qc_repository import QCRepository

class DashboardService:
    def __init__(self, session: Session):
        self.qc_repo = QCRepository(session)

    def get_summary(self) -> Dict[str, Any]:
        records = self.qc_repo.list_all()
        summary = {
            "total": len(records),
            "statuses": {},
            "major_flags": {},
            "critical_flags": {},
        }

        for r in records:
            data = json.loads(r.ml_results_json or "{}")
            status = data.get("status", "UNKNOWN")
            summary["statuses"][status] = summary["statuses"].get(status, 0) + 1

            for flag, value in data.get("major_flags", {}).items():
                if value:
                    summary["major_flags"][flag] = summary["major_flags"].get(flag, 0) + 1

            for flag, value in data.get("critical_flags", {}).items():
                if value:
                    summary["critical_flags"][flag] = summary["critical_flags"].get(flag, 0) + 1

        return summary

    def get_patient_dashboard(self, patient_id: str) -> List[Dict[str, Any]]:
        records = self.qc_repo.list_by_patient(patient_id)
        result = []

        for r in records:
            data = json.loads(r.ml_results_json or "{}")
            result.append({
                "exam_id": r.exam_id,
                "status": data.get("status"),
                "applied_fixes": data.get("applied_fixes", []),
                "major_flags": data.get("major_flags", {}),
                "critical_flags": data.get("critical_flags", {}),
            })

        return result

    def get_exam_dashboard(self, exam_id: int) -> Dict[str, Any]:
        records = self.qc_repo.list_by_exam(exam_id)
        if not records:
            return {}

        r = records[0]  # обычно один QCRecord на exam
        data = json.loads(r.ml_results_json or "{}")
        return {
            "exam_id": r.exam_id,
            "status": data.get("status"),
            "applied_fixes": data.get("applied_fixes", []),
            "major_flags": data.get("major_flags", {}),
            "critical_flags": data.get("critical_flags", {}),
        }
