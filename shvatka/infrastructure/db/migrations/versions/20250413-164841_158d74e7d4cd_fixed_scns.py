"""fixed scns

Revision ID: 158d74e7d4cd
Revises: f3157300bc04
Create Date: 2025-04-13 16:48:41.770588

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "158d74e7d4cd"
down_revision = "f3157300bc04"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][2]['time'] = '30'
        where name_id = 'game_131-lvl_4'
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][2]['hint'] =
         '[{"type": "text", "text":
         "Google 55.5923249, 37.9014795 Яндекс 55.592315, 37.901592"}]'::jsonb
        where name_id = 'game_130-lvl_6'
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][3]['time'] = '45'::jsonb
        where name_id = 'game_127-lvl_10'
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][4]['hint'] =
            '[{"type": "text", "text": "SHНЕВКУСНОИГРУСТНО"}]'::jsonb
        where name_id = 'game_125-lvl_2';
        """
        )
    )
    op.execute(
        sa.text(
            """
       update levels
       set scenario['time_hints'][4]['hint'] = '[{"type": "text", "text": "SHКАПКЕЙК"}]'::jsonb
       where name_id = 'game_125-lvl_3';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][4]['hint'] = '[{"type": "text", "text": "SHЧЕКАПНИСЬ"}]'::jsonb
        where name_id = 'game_125-lvl_4';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][4]['hint'] = '[{"type": "text", "text": "SHЭСАШ"}]'::jsonb
        where name_id = 'game_125-lvl_5';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][4]['hint'] =
            '[{"type": "text", "text": "SHБУДЬКАКЧИСТОМЭН"}]'::jsonb
        where name_id = 'game_125-lvl_6';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][4]['hint'] =
            '[{"type": "text", "text": "SHБИОХАКИНГ"}]'::jsonb
        where name_id = 'game_125-lvl_7';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][4]['hint'] =
            '[{"type": "text", "text": "SHPRESSF"}]'::jsonb
        where name_id = 'game_125-lvl_8';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][4]['hint'] =
            '[{"type": "text", "text": "SHЛОЛКЕК"}]'::jsonb
        where name_id = 'game_125-lvl_9';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][4]['hint'] =
            '[{"type": "text", "text": "SHЗОЖНИКУЕЖНИК"}]'::jsonb
        where name_id = 'game_125-lvl_10';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][3]['hint'] =
            '[{"type": "text", "text": "SHБУДЬЗДОРОВ"}]'::jsonb
        where name_id = 'game_125-lvl_11';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][3]['hint'] =
            '[{"type": "text", "text": "SH1SQSH2DTSH3LMSH4EKSH5OVSH6CD"}]'::jsonb
        where name_id = 'game_125-lvl_12';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][4]['hint'] =
            '[{"type": "text", "text": "SHЗОЖНЫЕНЯШЕЧКИ"}]'::jsonb
        where name_id = 'game_125-lvl_13';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][0]['hint'] =
            '[{"type": "text", "text": "http://cxbatka.ru/images/games/ram/video/rickdance.mp4"}]'::jsonb
        where name_id = 'game_118-lvl_6';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][5]['time'] = '60'::jsonb
        where name_id = 'game_117-lvl_15';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set
            scenario['time_hints'][1]['hint'] =
                '[{"type": "text", "text": "http://cxbatka.ru/images/games/apofimg/5ide02.mp4"}]'::jsonb,
            scenario['time_hints'][2]['hint'] =
                '[{"type": "text", "text": "http://cxbatka.ru/images/games/apofimg/v1de01.mp4"}]'::jsonb
        where name_id = 'game_115-lvl_13';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][2]['hint'] =
            '[{"type": "text", "text": "https://savepic.net/10028847.jpg"}]'::jsonb
        where name_id = 'game_104-lvl_6';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][3]['hint'] =
            '[{"type": "text", "text": "<a href=\\"https://maps.app.goo.gl/p1JL9jeZTCyus4fT7\\">Координаты</a>"}]'::jsonb
        where name_id = 'game_96-lvl_5';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][3]['hint'] =
            '[{"type": "text", "text":
            "<a href=\\"https://maps.app.goo.gl/4D4egcbChPboqbmX6\\">Тутки</a>"}]'
            ::jsonb
        where name_id = 'game_96-lvl_10';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][4]['time'] = '61'::jsonb
        where name_id = 'game_66-lvl_4';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'] = scenario['time_hints'] - 4
        where name_id = 'game_47-lvl_7';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][0]['hint'] =
            '[{"type": "text", "text": "&nbsp;"}]'::jsonb
        where name_id = 'game_45-lvl_3';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][0]['hint'] =
            '[{"type": "text", "text":
            "Задание 3 \\n<b>Средний</b> \\nФормат ключа: SH(слово на русском)"}]'
            ::jsonb
        where name_id = 'game_43-lvl_10';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][0]['hint'] =
            '[{"type": "text", "text":
            "http://www.youtube.com/v/qyss5RvaAso?fs=1&hl=ru_RU&rel=0"}]'::jsonb
        where name_id = 'game_43-lvl_24';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][3]['time'] = '60'::jsonb
        where name_id = 'game_29-lvl_1';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][0]['hint'] =
            '[{"type": "text", "text":
            "<a href=\\"http://www.nik0las.ru/cgi-bin/timer.py\\">Музыкальная пауза</a>"
            }]'::jsonb
        where name_id = 'game_27-lvl_10';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['conditions'] =
            '[{"keys": ["SHКАЖДЫЙМОЖЕТСТАТЬПИЛОТОМ"], "type": "WIN_KEY"}]'
                ::jsonb
        where name_id = 'game_26-lvl_11';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][6]['time'] = '90'::jsonb
        where name_id = 'game_23-lvl_9';
        """
        )
    )


def downgrade():
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][2]['time'] = '-1'
        where name_id = 'game_131-lvl_4'
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][2]['hint'] = '[]'::jsonb
        where name_id = 'game_130-lvl_6'
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][3]['time'] = '-1'::jsonb
        where name_id = 'game_127-lvl_10'
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][4]['hint'] = '[]'::jsonb
        where name_id = 'game_125-lvl_2';
        """
        )
    )
    op.execute(
        sa.text(
            """
       update levels
       set scenario['time_hints'][4]['hint'] = '[]'::jsonb
       where name_id = 'game_125-lvl_3';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][4]['hint'] = '[]'::jsonb
        where name_id = 'game_125-lvl_4';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][4]['hint'] = '[]'::jsonb
        where name_id = 'game_125-lvl_5';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][4]['hint'] = '[]'::jsonb
        where name_id = 'game_125-lvl_6';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][4]['hint'] = '[]'::jsonb
        where name_id = 'game_125-lvl_7';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][4]['hint'] = '[]'::jsonb
        where name_id = 'game_125-lvl_8';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][4]['hint'] = '[]'::jsonb
        where name_id = 'game_125-lvl_9';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][4]['hint'] = '[]'::jsonb
        where name_id = 'game_125-lvl_10';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][3]['hint'] = '[]'::jsonb
        where name_id = 'game_125-lvl_11';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][3]['hint'] = '[]'::jsonb
        where name_id = 'game_125-lvl_12';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][4]['hint'] = '[]'::jsonb
        where name_id = 'game_125-lvl_13';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][0]['hint'] = '[]'::jsonb
        where name_id = 'game_118-lvl_6';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][5]['time'] = '-1'::jsonb
        where name_id = 'game_117-lvl_15';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set
            scenario['time_hints'][1]['hint'] = '[]'::jsonb,
            scenario['time_hints'][2]['hint'] = '[]'::jsonb
        where name_id = 'game_115-lvl_13';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][2]['hint'] = '[]'::jsonb
        where name_id = 'game_104-lvl_6';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][3]['hint'] = '[]'::jsonb
        where name_id = 'game_96-lvl_5';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][3]['hint'] = '[]'::jsonb
        where name_id = 'game_96-lvl_10';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][4]['time'] = '-1'::jsonb
        where name_id = 'game_66-lvl_4';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][4] = '{"hint": [], "time": 91}'::jsonb
        where name_id = 'game_47-lvl_7';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][0]['hint'] = '[]'::jsonb
        where name_id = 'game_45-lvl_3';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][0]['hint'] = '[]'::jsonb
        where name_id = 'game_43-lvl_10';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][0]['hint'] = '[]'::jsonb
        where name_id = 'game_43-lvl_10';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][0]['hint'] = '[]'::jsonb
        where name_id = 'game_43-lvl_24';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][3]['time'] = '-1'::jsonb
        where name_id = 'game_29-lvl_1';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][0]['hint'] = '[]'::jsonb
        where name_id = 'game_27-lvl_10';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['conditions'] = '[]'::jsonb
        where name_id = 'game_26-lvl_11';
        """
        )
    )
    op.execute(
        sa.text(
            """
        update levels
        set scenario['time_hints'][6]['time'] = '-1'::jsonb
        where name_id = 'game_23-lvl_9';
        """
        )
    )
