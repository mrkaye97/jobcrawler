"""Adds users table
Revision ID: a0658319f516
Revises: 0ed26108783a
Create Date: 2023-04-18 16:06:45.335472

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a0658319f516'
down_revision = '0ed26108783a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(length=256), nullable=False),
        sa.Column('last_name', sa.String(length=256), nullable=False),
        sa.Column('email', sa.String(length=256), nullable=False, unique = True),
        sa.Column('password', sa.String(length=256), nullable=False, unique = True)
    )

def downgrade():
    op.drop_table('users')

