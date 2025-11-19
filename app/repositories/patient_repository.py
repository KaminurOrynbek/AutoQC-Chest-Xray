from sqlmodel import Session, select
from app.models.patients import Patient

class PatientRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, patient: Patient) -> Patient:
        self.session.add(patient)
        self.session.commit()
        self.session.refresh(patient)
        return patient

    def get_all(self) -> list[Patient]:
        return self.session.exec(select(Patient)).all()

    def get_by_id(self, patient_id: str) -> Patient | None:
        statement = select(Patient).where(Patient.patient_id == patient_id)
        return self.session.exec(statement).first()

    def update(self, patient: Patient) -> Patient:
        self.session.add(patient)
        self.session.commit()
        self.session.refresh(patient)
        return patient

    def delete(self, patient: Patient):
        self.session.delete(patient)
        self.session.commit()
