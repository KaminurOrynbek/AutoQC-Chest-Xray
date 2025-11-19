from fastapi import FastAPI, Depends
from sqlmodel import SQLModel, Session
from app.config.db import engine, get_session, init_db

# Роутеры
from app.api.auth.auth import router as auth_router
from app.api.admin.users import router as admin_users_router
from app.api.patient import patients
# Создаем приложение
app = FastAPI(title="AutoQC Chest Xray API")

# Инициализация БД
@app.on_event("startup")
def on_startup():
    init_db()

# Подключаем роутеры
app.include_router(auth_router)
app.include_router(admin_users_router, prefix="/admin")
app.include_router(patients.router, prefix="/patients")
# Пример эндпоинта здоровья
@app.get("/health")
def health():
    return {"status": "ok"}

# Пример использования сессии
@app.get("/test-db")
def test_db(session: Session = Depends(get_session)):
    return {"tables": list(SQLModel.metadata.tables.keys())}
