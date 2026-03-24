"""migrate key bonus to effects

Revision ID: d7e9e75ff5a8
Revises: 7e98407ed5e8
Create Date: 2026-02-20 23:39:11.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "d7e9e75ff5a8"
down_revision = "7e98407ed5e8"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        WITH scn AS (
            SELECT jsonb_set(
                l.scenario::JSONB,
                '{conditions}',
                (
                    SELECT jsonb_agg(
                        CASE
                            WHEN cond->>'type' = 'BONUS_KEY' THEN
                                jsonb_build_object(
                                    'type', 'EFFECTS',
                                    'keys', jsonb_build_array(key->>'text'),
                                    'effects', jsonb_build_object(
                                        'id', uuidv7(),
                                        'bonus_minutes', (key->>'bonus_minutes')::float,
                                        'level_up', false,
                                        'hints_', '[]'::jsonb,
                                        'next_level', null
                                    )
                                )
                            ELSE cond
                        END
                    )
                    FROM (
                        SELECT jsonb_array_elements(l.scenario::JSONB->'conditions') AS cond
                    ) conditions_array
                    CROSS JOIN LATERAL (
                        SELECT jsonb_array_elements(cond->'keys') AS key
                        WHERE cond->>'type' = 'BONUS_KEY'
                        UNION ALL
                        SELECT NULL AS key
                        WHERE cond->>'type' != 'BONUS_KEY'
                    ) keys_array
                    WHERE cond->>'type' != 'BONUS_KEY' OR key IS NOT NULL
                )
            ) AS scenario,
            l.id
            FROM levels AS l
            WHERE l.scenario::JSONB->'conditions' @> '[{"type": "BONUS_KEY"}]'::jsonb
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
            SELECT jsonb_set(
                l.scenario::JSONB,
                '{conditions}',
                (
                    SELECT COALESCE(jsonb_agg(cond), '[]'::jsonb)
                    FROM (
                        SELECT jsonb_array_elements(l.scenario::JSONB->'conditions') AS cond
                    ) conditions_array
                    WHERE NOT (
                        cond->>'type' = 'EFFECTS'
                        AND (cond->'effect'->>'bonus_minutes') IS NOT NULL
                        AND (cond->'effect'->>'bonus_minutes')::float != 0
                        AND (cond->'effect'->>'level_up')::boolean = false
                    )
                )
            ) AS scenario_without_effects,
            (
                SELECT COALESCE(
                    (
                        SELECT jsonb_build_object(
                            'type', 'BONUS_KEY',
                            'keys', jsonb_agg(
                                jsonb_build_object(
                                    'text', key_text,
                                    'bonus_minutes', bonus_minutes
                                )
                            )
                        )
                        FROM (
                            SELECT
                                (cond->'effect'->>'bonus_minutes')::float AS bonus_minutes,
                                jsonb_array_elements_text(cond->'keys') AS key_text
                            FROM (
                                SELECT jsonb_array_elements(
                                   l.scenario::JSONB->'conditions'
                                ) AS cond
                            ) conditions_array
                            WHERE cond->>'type' = 'EFFECTS'
                                AND (cond->'effect'->>'bonus_minutes') IS NOT NULL
                                AND (cond->'effect'->>'bonus_minutes')::float != 0
                                AND (cond->'effect'->>'level_up')::boolean = false
                        ) bonus_keys_data
                        HAVING count(*) > 0
                    ),
                    '[]'::jsonb
                )
            ) AS bonus_condition,
            l.id
            FROM levels AS l
            WHERE EXISTS (
                SELECT 1
                FROM jsonb_array_elements(l.scenario::JSONB->'conditions') AS cond
                WHERE cond->>'type' = 'EFFECTS'
                    AND (cond->'effect'->>'bonus_minutes') IS NOT NULL
                    AND (cond->'effect'->>'bonus_minutes')::float != 0
                    AND (cond->'effect'->>'level_up')::boolean = false
            )
        )
        UPDATE levels lvl
        SET scenario = CASE
            WHEN scn.bonus_condition != '[]'::jsonb THEN
                jsonb_set(
                    scn.scenario_without_effects,
                    '{conditions}',
                    scn.scenario_without_effects->'conditions'
                        || jsonb_build_array(scn.bonus_condition)
                )
            ELSE
                scn.scenario_without_effects
        END
        FROM scn
        WHERE scn.id = lvl.id
        """
    )
