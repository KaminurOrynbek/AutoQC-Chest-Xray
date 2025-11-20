"""Change patient_id to string in exam

Revision ID: 1ac677e5716f
Revises: 0bf9ef0d3ec2
Create Date: 2025-11-20 03:36:52.061013

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ac677e5716f'
down_revision: Union[str, Sequence[str], None] = '0bf9ef0d3ec2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Сначала удаляем FK
    op.drop_constraint('exam_patient_id_fkey', 'exam', type_='foreignkey')
    # Меняем тип колонки
    op.alter_column('exam', 'patient_id',
               existing_type=sa.INTEGER(),
               type_=sa.String(),
               existing_nullable=False)
    # Создаем FK на patient.patient_id
    op.create_foreign_key('exam_patient_id_fkey', 'exam', 'patient', ['patient_id'], ['patient_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, 'exam', type_='foreignkey')
    op.create_foreign_key('exam_patient_id_fkey', 'exam', 'patient', ['patient_id'], ['id'])
    op.alter_column(
        'exam',
        'patient_id',
        existing_type=sa.String(),
        type_=sa.INTEGER(),
        existing_nullable=False
    )
