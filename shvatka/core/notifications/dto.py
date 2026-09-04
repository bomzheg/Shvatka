from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from shvatka.core.models.enums.notification import NotificationSeverity, NotificationType
from shvatka.core.models.enums.request import RequestStatus, RequestType


@dataclass
class Page[T]:
    items: Sequence[T]
    limit: int
    offset: int
    filters: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class Notification:
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

    @property
    def is_pending(self) -> bool:
        return self.status == RequestStatus.pending
