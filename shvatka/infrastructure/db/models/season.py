from __future__ import annotations

import typing
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shvatka.core.season import dto
from shvatka.infrastructure.db.models.base import Base

if typing.TYPE_CHECKING:
    from shvatka.infrastructure.db import models


class Season(Base):
    __tablename__ = "seasons"
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    year: Mapped[int] = mapped_column(nullable=False, unique=True)
    published_by_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    log_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    log_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    unpinned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    slots: Mapped[list[SeasonSlot]] = relationship(
        "SeasonSlot",
        back_populates="season",
        foreign_keys="SeasonSlot.season_id",
        order_by="SeasonSlot.date",
    )

    __table_args__ = (Index("ix__seasons__published_by_id", "published_by_id"),)

    def to_dto(self, slots: list[dto.Slot] | None = None) -> dto.Season:
        return dto.Season(
            id=self.id,
            year=self.year,
            published_by_id=self.published_by_id,
            published_at=self.published_at,
            updated_at=self.updated_at,
            slots=slots or [],
            log_chat_id=self.log_chat_id,
            log_message_id=self.log_message_id,
            unpinned_at=self.unpinned_at,
        )

    def to_dto_with_slots(self) -> dto.Season:
        return self.to_dto(slots=[slot.to_dto() for slot in self.slots])


class SeasonSlot(Base):
    __tablename__ = "season_slots"
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    season_id: Mapped[int] = mapped_column(
        ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("players.id", ondelete="SET NULL"), nullable=True
    )
    author_kind: Mapped[dto.SlotAuthorKind | None] = mapped_column(
        Enum(dto.SlotAuthorKind, name="slot_author_kind"), nullable=True
    )
    team_id: Mapped[int | None] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
    )
    game_id: Mapped[int | None] = mapped_column(
        ForeignKey("games.id", ondelete="SET NULL"), nullable=True
    )
    taken_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    season: Mapped[Season] = relationship(
        "Season", back_populates="slots", foreign_keys=[season_id]
    )
    owner: Mapped[models.Player | None] = relationship("Player", foreign_keys=[owner_id])
    team: Mapped[models.Team | None] = relationship("Team", foreign_keys=[team_id])
    game: Mapped[models.Game | None] = relationship("Game", foreign_keys=[game_id])
    orgs: Mapped[list[SeasonSlotOrg]] = relationship(
        "SeasonSlotOrg",
        back_populates="slot",
        foreign_keys="SeasonSlotOrg.slot_id",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix__season_slots__season_date", "season_id", "date"),
        Index("ix__season_slots__owner_id", "owner_id"),
        Index("ix__season_slots__team_id", "team_id"),
        # one game sits in at most one date; many dates may be free of games
        UniqueConstraint("game_id", name="uq__season_slots__game_id"),
    )

    def to_dto(self) -> dto.Slot:
        return dto.Slot(
            id=self.id,
            season_id=self.season_id,
            date=self.date,
            note=self.note,
            owner=self.owner.to_dto_user_prefetched() if self.owner else None,
            author_kind=self.author_kind,
            team=self.team.to_dto_chat_prefetched() if self.team else None,
            orgs=[org.player.to_dto_user_prefetched() for org in self.orgs if org.player],
            game=_linked_game(self.game),
            taken_at=self.taken_at,
        )


class SeasonSlotOrg(Base):
    __tablename__ = "season_slot_orgs"
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    slot_id: Mapped[int] = mapped_column(
        ForeignKey("season_slots.id", ondelete="CASCADE"), nullable=False
    )
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )

    slot: Mapped[SeasonSlot] = relationship(
        "SeasonSlot", back_populates="orgs", foreign_keys=[slot_id]
    )
    player: Mapped[models.Player] = relationship("Player", foreign_keys=[player_id])

    __table_args__ = (
        UniqueConstraint("slot_id", "player_id", name="uq__season_slot_orgs__slot_player"),
        Index("ix__season_slot_orgs__player_id", "player_id"),
    )


class SeasonChange(Base):
    """One recorded edit of a published season: the audit trail and the digest's source."""

    __tablename__ = "season_changes"
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    season_id: Mapped[int] = mapped_column(
        ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False
    )
    slot_id: Mapped[int | None] = mapped_column(
        ForeignKey("season_slots.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[str] = mapped_column(Text, nullable=False)
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("players.id", ondelete="SET NULL"), nullable=True
    )
    by_superuser: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="f")
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default="{}", default=dict
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index(
            "ix__season_changes__unpublished",
            "season_id",
            postgresql_where=text("published_at IS NULL"),
        ),
        Index("ix__season_changes__slot_id", "slot_id"),
        Index("ix__season_changes__actor_id", "actor_id"),
    )

    def to_dto(self) -> dto.ScheduleChange:
        return dto.ScheduleChange(
            id=self.id,
            season_id=self.season_id,
            type=dto.ChangeType[self.type],
            created_at=self.created_at,
            slot_id=self.slot_id,
            actor_id=self.actor_id,
            by_superuser=self.by_superuser,
            payload=dict(self.payload or {}),
            published_at=self.published_at,
        )


def _linked_game(game: models.Game | None) -> dto.LinkedGame | None:
    if game is None:
        return None
    return dto.LinkedGame(
        id=game.id,
        name=game.name,
        start_at=game.start_at,
        number=game.number,
    )
