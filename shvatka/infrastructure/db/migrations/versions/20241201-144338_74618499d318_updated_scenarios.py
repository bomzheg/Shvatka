"""updated scenarios

Revision ID: 74618499d318
Revises: 84b3c1dab323
Create Date: 2024-12-01 14:43:38.379748

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "74618499d318"
down_revision = "84b3c1dab323"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        WITH scn AS (
        SELECT jsonb_insert(
           l.scenario::JSONB,
           '{conditions}',
           jsonb_path_query_array(
               jsonb_build_array(
                   jsonb_build_object(
                       'type', 'WIN_KEY',
                       'keys', l.scenario::JSONB->'keys'
                   ),
                   jsonb_build_object(
                       'type', 'BONUS_KEY',
                       'keys', jsonb_extract_path(l.scenario::JSONB, 'bonus_keys')
                   )
               ),
               '$[*] ? (@.keys != null && @.keys.size() > 0)'
           )
        ) - 'keys' - 'bonus_keys' AS scenario,
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
            SELECT jsonb_insert(
                   jsonb_insert(
                       l.scenario::JSONB,
                       '{keys}',
                       (SELECT COALESCE(jsonb_agg(k), '[]') AS flattened_keys
                       FROM (
                           SELECT jsonb_array_elements(elem->'keys') AS k
                           FROM (
                                SELECT jsonb_array_elements(
                                   jsonb_path_query_array(
                                    l.scenario::JSONB,
                                    '$.conditions[*] ? (@.type == "WIN_KEY")'
                                   )
                                ) AS elem
                           ) sub_query
                       ) keys)
                   ),
                   '{bonus_keys}',
                   (SELECT COALESCE(jsonb_agg(k), '[]') AS flattened_keys
                   FROM (
                       SELECT jsonb_array_elements(elem->'keys') AS k
                       FROM (
                            SELECT jsonb_array_elements(
                               jsonb_path_query_array(
                                   l.scenario::JSONB,
                                   '$.conditions[*] ? (@.type == "BONUS_KEY")'
                               )
                            ) AS elem
                       ) sub_query
                   ) keys)
               ) - 'conditions' AS scenario,
               l.id
            FROM levels AS l
        )
        UPDATE levels lvl
        SET scenario = scn.scenario
        FROM scn
        WHERE scn.id = lvl.id
    """
    )
