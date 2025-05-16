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
    # Add the new 'read' column with default using batch mode for SQLite
    with op.batch_alter_table('message', recreate="always") as batch_op:
        batch_op.add_column(
            sa.Column('read', sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch_op.alter_column('read', server_default=None)  # remove server default after adding


def downgrade():
    with op.batch_alter_table('message', recreate="always") as batch_op:
        batch_op.drop_column('read')
