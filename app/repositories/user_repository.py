from app.models.users import User
from sqlmodel import Session, select
from typing import Optional, List

class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, user_id: int) -> Optional[User]:
        return self.session.exec(select(User).where(User.id == user_id)).first()

    def get_by_username(self, username: str) -> Optional[User]:
        return self.session.exec(select(User).where(User.username == username)).first()

    def get_first_user(self) -> Optional[User]:
        return self.session.exec(select(User)).first()

    def get_all(self) -> List[User]:
        return self.session.exec(select(User)).all()

    def add(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update(self, user_id: int, **kwargs) -> User:
        user = self.get(user_id)
        if not user:
            raise ValueError(f"User with id={user_id} not found")

        # обновляем только переданные поля
        for key, value in kwargs.items():
            setattr(user, key, value)

        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def delete(self, user: User):
        self.session.delete(user)
        self.session.commit()
