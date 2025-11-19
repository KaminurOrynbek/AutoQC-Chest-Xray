# app/services/auth_service.py
from app.repositories.user_repository import UserRepository
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, session):
        self.user_repo = UserRepository(session)

    def login(self, username: str, password: str):
        user = self.user_repo.get_by_username(username)
        if not user or not self._check_password(password, user.hashed_password):
            raise Exception("Invalid credentials")
        return {"username": user.username, "role": user.role}

    def _check_password(self, raw: str, hashed: str) -> bool:
        return pwd_context.verify(raw, hashed)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)
