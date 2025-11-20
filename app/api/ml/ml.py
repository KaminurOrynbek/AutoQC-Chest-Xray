from fastapi import APIRouter, UploadFile, File
from app.client.ml import ml_client

router = APIRouter(prefix="/ml", tags=["ml"])

@router.post("/qc")
async def run_ml_qc(file: UploadFile = File(...)):
    """
    Читаем файл и передаем байты в ML клиент.
    """
    image_bytes = await file.read()  # читаем как bytes
    return ml_client.qc(image_bytes, filename=file.filename, content_type=file.content_type)
