import os
import requests
from dotenv import load_dotenv
from PIL import Image
import io
import base64

load_dotenv()
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL")

class MLClient:
    def qc(self, image_bytes: bytes, filename: str = "image.png", content_type: str = "image/png"):
        """
        Отправляем изображение в ML сервис.
        image_bytes — байты файла.
        """
        try:
            files = {"file": (filename, image_bytes, content_type)}
            response = requests.post(f"{ML_SERVICE_URL}/qc/preprocess", files=files)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise RuntimeError(f"Ошибка при запросе к ML сервису: {e}")

    def decode_base64_image(self, b64_str: str) -> Image.Image:
        return Image.open(io.BytesIO(base64.b64decode(b64_str)))

# Создаем экземпляр клиента
ml_client = MLClient()
