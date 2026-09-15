"""add season schedule tables

Revision ID: c8f1a2b3d4e5
Revises: e1a3c5d7b9f2
Create Date: 2026-09-07 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "c8f1a2b3d4e5"
down_revision = "e1a3c5d7b9f2"
branch_labels = None
depends_on = None


slot_author_kind = sa.Enum("player", "team", name="slot_author_kind")


def upgrade():
    op.create_table(
        "seasons",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("published_by_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("log_chat_id", sa.BigInteger(), nullable=True),
        sa.Column("log_message_id", sa.BigInteger(), nullable=True),
        sa.Column("unpinned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["published_by_id"],
            ["players.id"],
            name=op.f("seasons_published_by_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__seasons")),
        sa.UniqueConstraint("year", name=op.f("uq__seasons__year")),
    )
    op.create_index("ix__seasons__published_by_id", "seasons", ["published_by_id"], unique=False)

    op.create_table(
        "season_slots",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("season_id", sa.BigInteger(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("owner_id", sa.BigInteger(), nullable=True),
        sa.Column("author_kind", slot_author_kind, nullable=True),
        sa.Column("team_id", sa.BigInteger(), nullable=True),
        sa.Column("game_id", sa.BigInteger(), nullable=True),
        sa.Column("taken_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["season_id"],
            ["seasons.id"],
            name=op.f("season_slots_season_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["players.id"],
            name=op.f("season_slots_owner_id_fkey"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["teams.id"],
            name=op.f("season_slots_team_id_fkey"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["game_id"],
            ["games.id"],
            name=op.f("season_slots_game_id_fkey"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__season_slots")),
        # at most one game per date, and a game sits in at most one date
        sa.UniqueConstraint("game_id", name="uq__season_slots__game_id"),
    )
    op.create_index(
        "ix__season_slots__season_date", "season_slots", ["season_id", "date"], unique=False
    )
    op.create_index("ix__season_slots__owner_id", "season_slots", ["owner_id"], unique=False)
    op.create_index("ix__season_slots__team_id", "season_slots", ["team_id"], unique=False)

    op.create_table(
        "season_slot_orgs",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("slot_id", sa.BigInteger(), nullable=False),
        sa.Column("player_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["slot_id"],
            ["season_slots.id"],
            name=op.f("season_slot_orgs_slot_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["player_id"],
            ["players.id"],
            name=op.f("season_slot_orgs_player_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__season_slot_orgs")),
        sa.UniqueConstraint("slot_id", "player_id", name="uq__season_slot_orgs__slot_player"),
    )
    op.create_index(
        "ix__season_slot_orgs__player_id", "season_slot_orgs", ["player_id"], unique=False
    )

    op.create_table(
        "season_changes",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("season_id", sa.BigInteger(), nullable=False),
        sa.Column("slot_id", sa.BigInteger(), nullable=True),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.BigInteger(), nullable=True),
        sa.Column("payload", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["season_id"],
            ["seasons.id"],
            name=op.f("season_changes_season_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["slot_id"],
            ["season_slots.id"],
            name=op.f("season_changes_slot_id_fkey"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["players.id"],
            name=op.f("season_changes_actor_id_fkey"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__season_changes")),
    )
    op.create_index(
        "ix__season_changes__unpublished",
        "season_changes",
        ["season_id"],
        unique=False,
        postgresql_where=sa.text("published_at IS NULL"),
    )
    op.create_index("ix__season_changes__slot_id", "season_changes", ["slot_id"], unique=False)
    op.create_index("ix__season_changes__actor_id", "season_changes", ["actor_id"], unique=False)


def downgrade():
    op.drop_index("ix__season_changes__actor_id", table_name="season_changes")
    op.drop_index("ix__season_changes__slot_id", table_name="season_changes")
    op.drop_index("ix__season_changes__unpublished", table_name="season_changes")
    op.drop_table("season_changes")
    op.drop_index("ix__season_slot_orgs__player_id", table_name="season_slot_orgs")
    op.drop_table("season_slot_orgs")
    op.drop_index("ix__season_slots__team_id", table_name="season_slots")
    op.drop_index("ix__season_slots__owner_id", table_name="season_slots")
    op.drop_index("ix__season_slots__season_date", table_name="season_slots")
    op.drop_table("season_slots")
    op.drop_index("ix__seasons__published_by_id", table_name="seasons")
    op.drop_table("seasons")
    slot_author_kind.drop(op.get_bind(), checkfirst=False)
