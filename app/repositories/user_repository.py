from app.models.users import User
from sqlmodel import Session, select
from typing import List, Optional

class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_username(self, username: str) -> Optional[User]:
        return self.session.exec(select(User).where(User.username == username)).first()

    def get_first_user(self) -> Optional[User]:
        """Возвращает любого пользователя, если есть"""
        return self.session.exec(select(User)).first()

    def get_all(self) -> List[User]:
        """Возвращает список всех пользователей"""
        return self.session.exec(select(User)).all()

    def add(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
