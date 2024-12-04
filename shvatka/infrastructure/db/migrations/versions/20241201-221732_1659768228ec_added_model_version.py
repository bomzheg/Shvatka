"""added model-version

Revision ID: 1659768228ec
Revises: 74618499d318
Create Date: 2024-12-01 22:17:32.958776

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "1659768228ec"
down_revision = "74618499d318"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
       WITH scn AS (
        SELECT jsonb_insert(
           l.scenario::JSONB,
           '{__model_version__}',
           '1'
        ) AS scenario,
        l.id
        FROM levels AS l
    )
    UPDATE levels lvl
    SET scenario = scn.scenario
    FROM scn
    WHERE scn.id = lvl.id
    """
    )


def downgrade():
    op.execute(
        """
       WITH scn AS (
        SELECT
           l.scenario::JSONB - '__model_version__' AS scenario,
        l.id
        FROM levels AS l
    )
    UPDATE levels lvl
    SET scenario = scn.scenario
    FROM scn
    WHERE scn.id = lvl.id
    """
    )
