"""change is_correct to type

Revision ID: 84b3c1dab323
Revises: fb383262d07c
Create Date: 2023-05-28 14:09:18.243386

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "84b3c1dab323"
down_revision = "fb383262d07c"
branch_labels = None
depends_on = None

log_keys = sa.table(
    "log_keys",
    sa.Column("type", sa.Text, nullable=False),
    sa.Column("is_correct", sa.BOOLEAN, nullable=False),
)


def upgrade():
    op.add_column("log_keys", sa.Column("type", sa.Text()))
    op.execute(
        log_keys.update().values(type="wrong").where(log_keys.c.is_correct == False)  # noqa: E712
    )
    op.execute(
        log_keys.update().values(type="simple").where(log_keys.c.is_correct == True)  # noqa: E712
    )
    op.alter_column("log_keys", "type", nullable=False)
    op.drop_column("log_keys", "is_correct")


def downgrade():
    op.add_column(
        "log_keys", sa.Column("is_correct", sa.BOOLEAN(), autoincrement=False, nullable=True)
    )
    op.execute(log_keys.update().values(is_correct=(log_keys.c.type == "simple")))
    op.alter_column("log_keys", "is_correct", nullable=False)
    op.drop_column("log_keys", "type")
