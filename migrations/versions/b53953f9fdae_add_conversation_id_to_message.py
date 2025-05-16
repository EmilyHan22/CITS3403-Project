"""add conversation_id to Message

Revision ID: b53953f9fdae
Revises: eb7430127cc2
Create Date: 2025-05-16 02:18:34.673751

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b53953f9fdae'
down_revision = 'eb7430127cc2'
branch_labels = None
depends_on = None


def upgrade():
    # 1) add the new non-nullable column
    op.add_column(
        'message',
        sa.Column('conversation_id', sa.Integer(), nullable=False)
    )
    # 2) name and create the FK constraint to conversation.id
    op.create_foreign_key(
        'fk_message_conversation',
        'message', 'conversation',
        ['conversation_id'], ['id']
    )
    # 3) drop the old recipient_id column
    op.drop_column('message', 'recipient_id')


def downgrade():
    # 1) re-add the old column (as nullable so downgrade can run)
    op.add_column(
        'message',
        sa.Column('recipient_id', sa.Integer(), nullable=True)
    )
    # 2) drop our new FK
    op.drop_constraint('fk_message_conversation', 'message', type_='foreignkey')
    # 3) drop the conversation_id column
    op.drop_column('message', 'conversation_id')

