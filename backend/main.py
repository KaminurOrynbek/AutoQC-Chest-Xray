from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel
import os


from backend.db import engine, init_db
from backend.auth import router as auth_router
from backend.routers.records import router as records_router
from backend.routers.analytics import router as analytics_router
from backend.routers.reports import router as reports_router


app = FastAPI(title="CXR QC Backend")

origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# create upload dir if missing
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(records_router, prefix="/records", tags=["records"])
app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
app.include_router(reports_router, prefix="/reports", tags=["reports"])


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {"message": "CXR QC Backend running"}
