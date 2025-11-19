from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.config.db import engine
from app.services.patient_service import PatientService
from app.models.patients import Patient

router = APIRouter(prefix="/patients", tags=["Patients"])

# Dependency
def get_patient_service():
    with Session(engine) as session:
        yield PatientService(session)

# Create new patient
@router.post("/")
def create_patient(patient_data: Patient, service: PatientService = Depends(get_patient_service)):
    return service.create_patient(patient_data.dict())

# Get all patients
@router.get("/")
def get_patients(service: PatientService = Depends(get_patient_service)):
    return service.get_patients()

# Get patient by patient_id
@router.get("/{patient_id}")
def get_patient(patient_id: str, service: PatientService = Depends(get_patient_service)):
    patient = service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

# Update patient
@router.put("/{patient_id}")
def update_patient(patient_id: str, update_data: dict, service: PatientService = Depends(get_patient_service)):
    patient = service.update_patient(patient_id, update_data)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

# Delete patient
@router.delete("/{patient_id}")
def delete_patient(patient_id: str, service: PatientService = Depends(get_patient_service)):
    success = service.delete_patient(patient_id)
    if not success:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"status": "success", "message": "Patient deleted"}
