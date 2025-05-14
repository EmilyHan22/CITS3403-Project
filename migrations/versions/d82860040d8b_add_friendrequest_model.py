"""Add FriendRequest model

Revision ID: d82860040d8b
Revises: e0b90387dda0
Create Date: 2025-05-14 16:59:32.720324

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd82860040d8b'
down_revision = 'e0b90387dda0'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'friend_request',
        sa.Column('id',             sa.Integer(),      primary_key=True),
        sa.Column('from_user_id',   sa.Integer(),      sa.ForeignKey('user.id'), nullable=False),
        sa.Column('to_user_id',     sa.Integer(),      sa.ForeignKey('user.id'), nullable=False),
        sa.Column('status',         sa.String(20),     nullable=False, server_default='pending'),
        sa.Column('created_at',     sa.DateTime(),      nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('from_user_id','to_user_id', name='uq_friend_request')
    )

def downgrade():
    op.drop_constraint('uq_friend_request', 'friend_request', type_='unique')
    op.drop_table('friend_request')

