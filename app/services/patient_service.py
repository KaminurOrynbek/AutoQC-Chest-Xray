from sqlmodel import Session, select
from app.models.patients import Patient
from app.models.exams import Exam
from app.repositories.patient_repository import PatientRepository
from fastapi import HTTPException
from app.models.qc_records import QCRecord

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

        session: Session = self.repo.session

        # 1️⃣ Получаем все экзамены пациента
        exams = session.exec(select(Exam).where(Exam.patient_id == patient_id)).all()

        for exam in exams:
            # 2️⃣ Удаляем все QC-записи для экзамена
            qc_records = session.exec(select(QCRecord).where(QCRecord.exam_id == exam.id)).all()
            for qc in qc_records:
                session.delete(qc)

            # 3️⃣ Удаляем сам экзамен
            session.delete(exam)

        # 4️⃣ Удаляем пациента
        session.delete(patient)
        session.commit()

        return True
