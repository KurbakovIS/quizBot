"""empty message

Revision ID: 5dc6b7ae480c
Revises: fd7d8259aa0f
Create Date: 2024-08-02 11:34:14.257348

"""
from alembic import op
import sqlalchemy as sa
from src.database.custom_types import FileType


# revision identifiers, used by Alembic.
revision = '5dc6b7ae480c'
down_revision = 'fd7d8259aa0f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('levels', sa.Column('number', sa.Integer(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('levels', 'number')
    # ### end Alembic commands ###
