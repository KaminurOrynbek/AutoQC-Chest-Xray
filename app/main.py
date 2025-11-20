from fastapi import FastAPI, Depends
from sqlmodel import SQLModel, Session
from app.config.db import engine, get_session, init_db
from fastapi.middleware.cors import CORSMiddleware

# Роутеры
from app.api.auth.auth import router as auth_router
from app.api.admin.users import router as admin_users_router
from app.api.patient import patients
from app.api.exam import exams
from app.api.qc import qc
from app.api.ml import ml
from app.api.dashboard import dashboard


# Создаем приложение
app = FastAPI(title="AutoQC Chest Xray API")

# Инициализация БД
@app.on_event("startup")
def on_startup():
    init_db()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],  # фронтенд
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(auth_router)
app.include_router(admin_users_router, prefix="/admin")
app.include_router(patients.router, prefix="/patients")
app.include_router(exams.router, prefix="/exams")
app.include_router(qc.router, prefix="/qc")
app.include_router(ml.router, prefix="/ml")
app.include_router(dashboard.router, prefix="/dashboard")

# Пример эндпоинта здоровья
@app.get("/health")
def health():
    return {"status": "ok"}

# Пример использования сессии
@app.get("/test-db")
def test_db(session: Session = Depends(get_session)):
    return {"tables": list(SQLModel.metadata.tables.keys())}
