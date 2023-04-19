"""link stuff to users

Revision ID: b8e56d0558ce
Revises: 28b1ddaa007b
Create Date: 2023-04-19 18:15:22.504428

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8e56d0558ce'
down_revision = '28b1ddaa007b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('searches', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_searches_company_id'), ['company_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_searches_user_id'), ['user_id'], unique=False)
        batch_op.create_foreign_key(None, 'users', ['user_id'], ['id'])

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('last_name')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_name', sa.VARCHAR(length=128), autoincrement=False, nullable=True))

    with op.batch_alter_table('searches', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_searches_user_id'))
        batch_op.drop_index(batch_op.f('ix_searches_company_id'))
        batch_op.drop_column('user_id')

    # ### end Alembic commands ###
