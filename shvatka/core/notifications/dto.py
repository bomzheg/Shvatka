from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from shvatka.core.models.enums.notification import NotificationType, NotificationSeverity
from shvatka.core.models.enums.request import RequestType, RequestStatus


@dataclass
class Page[T]:
    """A slice of a listing: the fetched items plus the applied window and filters."""

    items: Sequence[T]
    limit: int
    offset: int
    filters: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class Notification:
    """One inbox item delivered to exactly one recipient."""

    id: int
    recipient_id: int
    type: NotificationType
    severity: NotificationSeverity
    created_at: datetime
    payload: dict[str, Any] = field(default_factory=dict)
    actor_id: int | None = None
    request_id: int | None = None
    read_at: datetime | None = None

    @property
    def is_read(self) -> bool:
        return self.read_at is not None


@dataclass
class ActionRequest:
    """A user-to-user request with a lifecycle (pending -> accepted/declined/...)."""

    id: int
    type: RequestType
    status: RequestStatus
    initiator_id: int
    created_at: datetime
    payload: dict[str, Any] = field(default_factory=dict)
    target_player_id: int | None = None
    team_id: int | None = None
    game_id: int | None = None
    responder_id: int | None = None
    responded_at: datetime | None = None
    expires_at: datetime | None = None
    bot_messages: list[dict[str, int]] = field(default_factory=list)

    @property
    def is_pending(self) -> bool:
        return self.status == RequestStatus.pending
