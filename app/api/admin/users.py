from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.config.db import get_session
from app.services.user_service import UserService
from app.models.users import User

router = APIRouter(prefix="/admin/users", tags=["admin"])

@router.get("/")
def list_users(session: Session = Depends(get_session)):
    service = UserService(session)
    return service.list_users()

@router.get("/{user_id}")
def get_user(user_id: int, session: Session = Depends(get_session)):
    service = UserService(session)
    try:
        return service.get_user(user_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/")
def create_user(user: User, session: Session = Depends(get_session)):
    service = UserService(session)
    return service.create_user(user)

@router.put("/{user_id}")
def update_user(user_id: int, user: User, session: Session = Depends(get_session)):
    service = UserService(session)
    return service.update_user(user_id, **user.dict(exclude_unset=True))

@router.delete("/{user_id}")
def delete_user(user_id: int, session: Session = Depends(get_session)):
    service = UserService(session)
    service.delete_user(user_id)
    return {"detail": "User deleted"}
