from __future__ import annotations

import typing
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shvatka.core.season import dto
from shvatka.infrastructure.db.models.base import Base

if typing.TYPE_CHECKING:
    from shvatka.infrastructure.db.models.season_slot import SeasonSlot


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
        order_by="SeasonSlot.slot_date",
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
