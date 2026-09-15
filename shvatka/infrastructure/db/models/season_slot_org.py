from __future__ import annotations

import typing

from sqlalchemy import BigInteger, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shvatka.infrastructure.db.models.base import Base

if typing.TYPE_CHECKING:
    from shvatka.infrastructure.db import models
    from shvatka.infrastructure.db.models.season_slot import SeasonSlot


class SeasonSlotOrg(Base):
    """A player the slot owner names as a co-organizer of the game that does not exist yet."""

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
