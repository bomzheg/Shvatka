"""add all shvatka tables

Revision ID: 555d635df99f
Revises: 56df5c6b0df6
Create Date: 2022-07-18 22:16:46.815679

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '555d635df99f'
down_revision = '56df5c6b0df6'
branch_labels = None
depends_on = None

game_status = sa.Enum(
    'underconstruction',
    'ready',
    'getting_waivers',
    'started',
    'finished',
    'complete',
    name='game_status',
)

waiver_status = sa.Enum(
    'yes', 'no', 'think', 'revoked', 'not_allowed', name='played',
)


def upgrade():
    op.create_table(
        'files_info',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.Text(), nullable=True),
        sa.Column('file_path', sa.Text(), nullable=True),
        sa.Column('guid_', sa.Text(), nullable=True),
        sa.Column('original_filename', sa.Text(), nullable=True),
        sa.Column('extension', sa.Text(), nullable=True),
        sa.Column('content_type', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint("guid_"),
    )
    op.create_table(
        'players',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('can_be_author', sa.Boolean(), server_default='f', nullable=False),
        sa.Column('promoted_by_id', sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['promoted_by_id'], ['players.id'], ),
        sa.UniqueConstraint("user_id"),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'games',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('status', game_status, nullable=False),
        sa.Column('start_at', sa.DateTime(), nullable=True),
        sa.Column('published_channel_id', sa.BigInteger(), nullable=True),
        sa.Column('manage_token', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['players.id'], ),
        sa.UniqueConstraint("name", "author_id"),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('chat_id', sa.BigInteger(), nullable=True),
        sa.Column('captain_id', sa.BigInteger(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['captain_id'], ['players.id'], ),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ),
        sa.UniqueConstraint("chat_id"),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'levels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name_id', sa.Text(), nullable=True),
        sa.Column('game_id', sa.Integer(), nullable=True),
        sa.Column('author_id', sa.BigInteger(), nullable=False),
        sa.Column('number_in_game', sa.Integer(), nullable=True),
        sa.Column('scenario', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['players.id'], ),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
        sa.UniqueConstraint("name_id", "author_id"),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'levels_times',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('level_number', sa.Integer(), nullable=True),
        sa.Column('start_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.UniqueConstraint("game_id", "team_id", "level_number"),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'log_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.BigInteger(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('level_number', sa.Integer(), nullable=True),
        sa.Column('enter_time', sa.DateTime(), nullable=True),
        sa.Column('key_text', sa.Text(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('is_duplicate', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'organizers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.BigInteger(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('can_spy', sa.Boolean(), nullable=True),
        sa.Column('can_see_log_keys', sa.Boolean(), nullable=True),
        sa.Column('can_validate_waivers', sa.Boolean(), nullable=True),
        sa.Column('deleted', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
        sa.UniqueConstraint("game_id", "player_id"),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'players_in_teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.BigInteger(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('date_joined', sa.DateTime(), nullable=True),
        sa.Column('role', sa.Text(), nullable=True),
        sa.Column('emoji', sa.Text(), nullable=True),
        sa.Column('date_left', sa.DateTime(), nullable=True),
        sa.Column('can_manage_waivers', sa.Boolean(), nullable=True),
        sa.Column('can_manage_players', sa.Boolean(), nullable=True),
        sa.Column('can_change_team_name', sa.Boolean(), nullable=True),
        sa.Column('can_add_players', sa.Boolean(), nullable=True),
        sa.Column('can_remove_players', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'waivers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.BigInteger(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.Text(), nullable=True),
        sa.Column('played', waiver_status, nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.UniqueConstraint("game_id", "team_id", "player_id"),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('waivers')
    op.drop_table('players_in_teams')
    op.drop_table('organizers')
    op.drop_table('log_keys')
    op.drop_table('levels_times')
    op.drop_table('levels')
    op.drop_table('teams')
    op.drop_table('games')
    op.drop_table('players')
    op.drop_table('files_info')
    game_status.drop(op.get_bind(), checkfirst=False)
    waiver_status.drop(op.get_bind(), checkfirst=False)
