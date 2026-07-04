from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from shvatka.core.models.enums.notification import NotificationType, NotificationSeverity
from shvatka.core.notifications import dto
from shvatka.infrastructure.db.models.base import Base


class Notification(Base):
    __tablename__ = "notifications"
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[NotificationSeverity] = mapped_column(
        Enum(NotificationSeverity, name="notification_severity"),
        nullable=False,
        server_default=NotificationSeverity.normal.name,
    )
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default="{}", default=dict
    )
    request_id: Mapped[int | None] = mapped_column(ForeignKey("action_requests.id"), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def to_dto(self) -> dto.Notification:
        return dto.Notification(
            id=self.id,
            recipient_id=self.recipient_id,
            type=NotificationType[self.type],
            severity=self.severity,
            created_at=self.created_at,
            payload=dict(self.payload or {}),
            actor_id=self.actor_id,
            request_id=self.request_id,
            read_at=self.read_at,
        )
