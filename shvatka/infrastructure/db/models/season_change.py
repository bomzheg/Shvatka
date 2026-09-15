from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from shvatka.core.season import dto
from shvatka.infrastructure.db.models.base import Base


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
            payload=dict(self.payload or {}),
            published_at=self.published_at,
        )
