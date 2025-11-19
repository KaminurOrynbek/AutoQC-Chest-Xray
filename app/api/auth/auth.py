from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from app.config.db import get_session
from app.models.users import User
from app.services.auth_service import AuthService

router = APIRouter(tags=["auth"])


@router.post("/auth/register")
def register(username: str, password: str, full_name: str, session: Session = Depends(get_session)):
    """
    Регистрирует первого админа в системе.
    После того как создан хотя бы один пользователь, регистрация запрещена.
    """
    auth_service = AuthService(session)

    # Проверяем, есть ли уже пользователи
    first_user = auth_service.user_repo.get_first_user()
    if first_user:
        raise HTTPException(status_code=403, detail="Регистрация доступна только для первого админа")

    # Хэшируем пароль
    hashed_password = auth_service.get_password_hash(password)

    # Создаем пользователя
    user = User(username=username, full_name=full_name, hashed_password=hashed_password, role="ADMIN")
    auth_service.user_repo.add(user)  # используем add из UserRepository

    return {"id": user.id, "username": user.username, "role": user.role}


@router.post("/auth/login")
def login(username: str, password: str, session: Session = Depends(get_session)):
    """
    Логин пользователя по username и password.
    """
    auth_service = AuthService(session)
    try:
        return auth_service.login(username, password)
    except Exception:
        raise HTTPException(status_code=401, detail="Неверные учётные данные")
