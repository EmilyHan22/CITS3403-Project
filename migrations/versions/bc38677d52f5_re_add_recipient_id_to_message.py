"""re_add_recipient_and_conversation_to_message

Revision ID: bc38677d52f5
Revises: b53953f9fdae
Create Date: 2025-05-16 02:xx:xx.xxxxxx
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'bc38677d52f5'
down_revision = 'b53953f9fdae'
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != 'sqlite':
        # add recipient FK
        op.create_foreign_key(
            'fk_message_recipient',
            source_table='message',
            referent_table='user',
            local_cols=['recipient_id'],
            remote_cols=['id'],
        )
        # add conversation FK
        op.create_foreign_key(
            'fk_message_conversation',
            source_table='message',
            referent_table='conversation',
            local_cols=['conversation_id'],
            remote_cols=['id'],
        )
    # on SQLite we skip, since it can't ALTER constraints in place

def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != 'sqlite':
        op.drop_constraint('fk_message_conversation', 'message', type_='foreignkey')
        op.drop_constraint('fk_message_recipient',   'message', type_='foreignkey')

