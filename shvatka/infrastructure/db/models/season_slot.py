from __future__ import annotations

import typing
from datetime import date, datetime

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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shvatka.core.season import dto
from shvatka.infrastructure.db.models.base import Base

if typing.TYPE_CHECKING:
    from shvatka.infrastructure.db import models
    from shvatka.infrastructure.db.models.season import Season
    from shvatka.infrastructure.db.models.season_slot_org import SeasonSlotOrg


class SeasonSlot(Base):
    __tablename__ = "season_slots"
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    season_id: Mapped[int] = mapped_column(
        ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False
    )
    slot_date: Mapped[date] = mapped_column(Date, nullable=False)
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
        Index("ix__season_slots__season_date", "season_id", "slot_date"),
        Index("ix__season_slots__owner_id", "owner_id"),
        Index("ix__season_slots__team_id", "team_id"),
        # one game sits in at most one date; many dates may be free of games
        UniqueConstraint("game_id", name="uq__season_slots__game_id"),
    )

    def to_dto(self) -> dto.Slot:
        return dto.Slot(
            id=self.id,
            season_id=self.season_id,
            slot_date=self.slot_date,
            note=self.note,
            owner=self.owner.to_dto_user_prefetched() if self.owner else None,
            author_kind=self.author_kind,
            team=self.team.to_dto_chat_prefetched() if self.team else None,
            orgs=[org.player.to_dto_user_prefetched() for org in self.orgs if org.player],
            game=_linked_game(self.game),
            taken_at=self.taken_at,
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
