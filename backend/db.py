from sqlmodel import create_engine, SQLModel, Session
import os

# Путь к файлу базы данных
DB_FILE = os.path.join(os.path.dirname(__file__), "database.db")
DATABASE_URL = f"sqlite:///{DB_FILE}"

# Создаём движок SQLAlchemy
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def init_db():
    """
    Инициализация базы данных:
    импортируем модели, чтобы SQLModel знал о таблицах,
    и создаём их при первом запуске.
    """
    from backend.models import User, ScanRecord, QCFinding, Report

    SQLModel.metadata.create_all(engine)


def get_session():
    """
    Возвращает сессию базы данных.
    Используется в зависимостях (Depends).
    """
    with Session(engine) as session:
        yield session
