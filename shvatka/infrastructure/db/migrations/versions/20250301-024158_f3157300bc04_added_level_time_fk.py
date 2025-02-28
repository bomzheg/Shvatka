"""added level-time fk

Revision ID: f3157300bc04
Revises: 149de95bb84e
Create Date: 2025-03-01 02:41:58.385413

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3157300bc04'
down_revision = '149de95bb84e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('log_keys', sa.Column('level_time_id', sa.Integer(), nullable=True))
    # next line update existing log_keys with level_time_id by same game_id, team_id and level_number
    op.execute(
        sa.text(
            """
            UPDATE log_keys
            SET level_time_id = (
                SELECT id
                FROM levels_times
                WHERE game_id = log_keys.game_id
                AND team_id = log_keys.team_id
                AND level_number = log_keys.level_number
                AND start_at <= log_keys.enter_time
                ORDER BY start_at DESC
                LIMIT 1
            )
            WHERE level_time_id IS NULL
            """
        )
    )
    op.create_foreign_key(op.f('log_keys_level_time_id_fkey'), 'log_keys', 'levels_times', ['level_time_id'], ['id'])


def downgrade():
    op.drop_constraint(op.f('log_keys_level_time_id_fkey'), 'log_keys', type_='foreignkey')
    op.drop_column('log_keys', 'level_time_id')
