from sqlmodel import Session
from app.models.patients import Patient
from app.repositories.patient_repository import PatientRepository

class PatientService:
    def __init__(self, session: Session):
        self.repo = PatientRepository(session)

    def create_patient(self, patient_data: dict) -> Patient:
        patient = Patient(**patient_data)
        return self.repo.create(patient)

    def get_patients(self) -> list[Patient]:
        return self.repo.get_all()

    def get_patient(self, patient_id: str) -> Patient | None:
        return self.repo.get_by_id(patient_id)

    def update_patient(self, patient_id: str, update_data: dict) -> Patient | None:
        patient = self.repo.get_by_id(patient_id)
        if not patient:
            return None
        for key, value in update_data.items():
            setattr(patient, key, value)
        return self.repo.update(patient)

    def delete_patient(self, patient_id: str) -> bool:
        patient = self.repo.get_by_id(patient_id)
        if not patient:
            return False
        self.repo.delete(patient)
        return True
