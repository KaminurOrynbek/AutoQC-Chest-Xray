import sys
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel
from alembic import context
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


config = context.config
DATABASE_URL = os.getenv("DATABASE_URL")

config.set_main_option("sqlalchemy.url", str(DATABASE_URL))

fileConfig(config.config_file_name)

# Импортируем модели — очень важно
from app.models.users import User
from app.models.patients import Patient
from app.models.exams import Exam
from app.models.qc_records import QCRecord

target_metadata = SQLModel.metadata


def run_migrations_offline():
    context.configure(
        url=str(DATABASE_URL),
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
