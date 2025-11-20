from app.repositories.user_repository import UserRepository
from app.models.users import User
from sqlmodel import Session
from typing import List

class UserService:
    def __init__(self, session: Session):
        self.user_repo = UserRepository(session)

    def list_users(self) -> List[User]:
        return self.user_repo.get_all()

    def get_user(self, user_id: int) -> User:
        user = self.user_repo.get(user_id)
        if not user:
            raise Exception(f"User {user_id} not found")
        return user

    def create_user(self, user: User) -> User:
        return self.user_repo.add(user)

    def update_user(self, user_id: int, **kwargs) -> User:
        # вызываем update напрямую с user_id и kwargs
        return self.user_repo.update(user_id, **kwargs)

    def delete_user(self, user_id: int):
        user = self.get_user(user_id)
        self.user_repo.delete(user)
