"""Add read flag to Message

Revision ID: 0cb719df6b1e
Revises: bc38677d52f5
Create Date: 2025-05-16 05:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0cb719df6b1e'
down_revision = 'bc38677d52f5'
branch_labels = None
depends_on = None

def upgrade():
    # 1) Add the new 'read' column, defaulting existing rows to False
    op.add_column(
        'message',
        sa.Column('read', sa.Boolean(), nullable=False, server_default=sa.false())
    )
    # 2) Remove the server_default so new inserts use your Python‐side default
    op.alter_column('message', 'read', server_default=None)


def downgrade():
    op.drop_column('message', 'read')

