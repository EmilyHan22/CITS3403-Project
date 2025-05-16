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
    with op.batch_alter_table('message', recreate='always') as batch_op:
        # Add the new column
        batch_op.add_column(sa.Column('conversation_id', sa.Integer(), nullable=False))
        # Create foreign key constraint
        batch_op.create_foreign_key('fk_message_conversation', 'conversation', ['conversation_id'], ['id'])
        # Drop the old column
        batch_op.drop_column('recipient_id')


def downgrade():
    with op.batch_alter_table('message', recreate='always') as batch_op:
        # Re-add the old column as nullable
        batch_op.add_column(sa.Column('recipient_id', sa.Integer(), nullable=True))
        # Drop the new foreign key
        batch_op.drop_constraint('fk_message_conversation', type_='foreignkey')
        # Drop the conversation_id column
        batch_op.drop_column('conversation_id')

