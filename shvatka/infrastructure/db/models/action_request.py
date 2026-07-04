from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from shvatka.core.models.enums.request import RequestType, RequestStatus
from shvatka.core.notifications import dto
from shvatka.infrastructure.db.models.base import Base


class ActionRequest(Base):
    __tablename__ = "action_requests"
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, name="request_status"),
        nullable=False,
        server_default=RequestStatus.pending.name,
    )
    initiator_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    target_player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    game_id: Mapped[int | None] = mapped_column(ForeignKey("games.id"), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default="{}", default=dict
    )
    responder_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dto(self) -> dto.ActionRequest:
        return dto.ActionRequest(
            id=self.id,
            type=RequestType[self.type],
            status=self.status,
            initiator_id=self.initiator_id,
            created_at=self.created_at,
            payload=dict(self.payload or {}),
            target_player_id=self.target_player_id,
            team_id=self.team_id,
            game_id=self.game_id,
            responder_id=self.responder_id,
            responded_at=self.responded_at,
            expires_at=self.expires_at,
        )
