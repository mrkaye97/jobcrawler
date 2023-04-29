"""Expand company URL column length

Revision ID: 1c71d812de2b
Revises: 5e3c5f0e7bad
Create Date: 2023-04-29 14:27:52.445585

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1c71d812de2b'
down_revision = '5e3c5f0e7bad'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('companies', schema=None) as batch_op:
        batch_op.alter_column('board_url',
               existing_type=sa.VARCHAR(length=128),
               type_=sa.String(length=2048),
               existing_nullable=False)
        batch_op.alter_column('job_posting_url_prefix',
               existing_type=sa.VARCHAR(length=128),
               type_=sa.String(length=2048),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('companies', schema=None) as batch_op:
        batch_op.alter_column('job_posting_url_prefix',
               existing_type=sa.String(length=2048),
               type_=sa.VARCHAR(length=128),
               existing_nullable=True)
        batch_op.alter_column('board_url',
               existing_type=sa.String(length=2048),
               type_=sa.VARCHAR(length=128),
               existing_nullable=False)

    # ### end Alembic commands ###