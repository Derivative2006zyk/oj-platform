"""add submission_kind and answer_data to submissions

Revision ID: e4f3ab6df0ae
Revises: 832a1234d0b7
Create Date: 2026-10-12 10:27:42.991629

"""
from sqlalchemy.dialects import postgresql
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4f3ab6df0ae'
down_revision: Union[str, None] = '832a1234d0b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'submissions',
        sa.Column('submission_kind', sa.String(length=20),
                  server_default='code', nullable=False),
    )
    op.add_column(
        'submissions',
        sa.Column('answer_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.alter_column('submissions', 'code', existing_type=sa.Text(), nullable=True)
    op.create_index(
        op.f('ix_submissions_submission_kind'),
        'submissions',
        ['submission_kind'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_submissions_submission_kind'), table_name='submissions')
    op.alter_column('submissions', 'code', existing_type=sa.Text(), nullable=False)
    op.drop_column('submissions', 'answer_data')
    op.drop_column('submissions', 'submission_kind')