from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from .enums.user_roles import UserRole

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(sa_column_kwargs={"unique": True, "nullable": False})
    full_name: Optional[str] = None
    hashed_password: str
    role: UserRole = Field(default=UserRole.ADMIN)
    created_at: datetime = Field(default_factory=datetime.utcnow)
