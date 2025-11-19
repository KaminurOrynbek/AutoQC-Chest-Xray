"""initial tables

Revision ID: 0bf9ef0d3ec2
Revises:
Create Date: 2025-11-19 23:41:53.029818

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0bf9ef0d3ec2'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'patient',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('patient_id', sa.String(), nullable=False, unique=True),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('birth_date', sa.Date(), nullable=False),
        sa.Column('sex', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('username', sa.String(), nullable=False, unique=True),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('role', sa.Enum('ADMIN', name='userrole'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'exam',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('patient_id', sa.Integer(), sa.ForeignKey('patient.id'), nullable=False),
        sa.Column('accession_number', sa.String(), nullable=False, unique=True),
        sa.Column('exam_date', sa.DateTime(), nullable=False),
        sa.Column('modality', sa.String(), nullable=False),
        sa.Column('view_type', sa.String(), nullable=False),
        sa.Column('device', sa.String(), nullable=False),
        sa.Column('technician', sa.String(), nullable=False),
        sa.Column('notes', sa.String(), nullable=True),
    )

    op.create_table(
        'qcrecord',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('exam_id', sa.Integer(), sa.ForeignKey('exam.id'), nullable=False),
        sa.Column('original_image_path', sa.String(), nullable=False),
        sa.Column('corrected_image_path', sa.String(), nullable=True),
        sa.Column('ml_results_json', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('qcrecord')
    op.drop_table('exam')
    op.drop_table('user')
    op.drop_table('patient')
