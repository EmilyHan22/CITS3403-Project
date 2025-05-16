"""Add recipient_id column to message

Revision ID: adca1a252d1b
Revises: 52417dec5f0f
Create Date: 2025-05-16 19:43:26.670397

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'adca1a252d1b'
down_revision = '52417dec5f0f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('message', sa.Column('recipient_id', sa.Integer(), nullable=False))

def downgrade():
    op.drop_column('message', 'recipient_id')
