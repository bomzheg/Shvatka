"""updated scenarios

Revision ID: 74618499d318
Revises: 84b3c1dab323
Create Date: 2024-12-01 14:43:38.379748

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "74618499d318"
down_revision = "84b3c1dab323"
branch_labels = None
depends_on = None

levels = sa.table(
    "levels",
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("scenario", postgresql.JSONB, nullable=False),
)


def upgrade():
    op.execute("""
        with scn as (
        select jsonb_insert(
                       l.scenario::jsonb,
                       '{conditions}',
                       jsonb_build_array(
                               jsonb_build_object(
                                       'type', 'WIN_KEY',
                                       'keys', l.scenario::jsonb->'keys'
                               ),
                               jsonb_build_object(
                                       'type', 'BONUS_KEY',
                                       'keys', jsonb_extract_path(l.scenario::jsonb, 'bonus_keys')
                               )
                       )
               ) - 'keys' - 'bonus_keys' as scenario,
               l.id
        from levels as l
    )
    update levels lvl
    set scenario = scn.scenario
    from scn
    where scn.id = lvl.id
    """)


def downgrade():
    op.execute("""
        with scn as (
            select jsonb_insert(
                           jsonb_insert(
                                   l.scenario::jsonb,
                                   '{keys}',
                                   l.scenario::jsonb -> 'conditions' -> 0 -> 'keys'
                           ),
                           '{bonus_keys}',
                           l.scenario::jsonb -> 'conditions' -> 1 -> 'keys'
                   ) - 'conditions' as scenario,
                   l.id
            from levels as l
        )
        update levels lvl
        set scenario = scn.scenario
        from scn
        where scn.id = lvl.id
    """)
