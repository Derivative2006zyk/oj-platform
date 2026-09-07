"""seed default categories

Revision ID: 8b23d3a4033d
Revises: f7993218dca9
Create Date: 2026-09-07 16:42:39.517222

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b23d3a4033d'
down_revision: Union[str, None] = 'f7993218dca9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO categories (name, sort_order) VALUES
        ('算法', 1),
        ('数学', 2),
        ('物理', 3),
        ('英语', 4),
        ('其他', 99)
    """)

def downgrade() -> None:
    op.execute("DELETE FROM categories WHERE name IN ('算法', '数学', '物理', '英语', '其他')")
