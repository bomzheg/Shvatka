from __future__ import annotations

from collections.abc import Collection, Sequence
from datetime import datetime
from typing import Any, Protocol

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.models.enums.notification import NotificationType, NotificationSeverity
from shvatka.core.models.enums.request import RequestType, RequestStatus
from shvatka.core.notifications import dto


class NotificationReader(Protocol):
    async def get_for_player(
        self,
        player_id: int,
        *,
        unread_only: bool = ...,
        limit: int = ...,
        offset: int = ...,
    ) -> Sequence[dto.Notification]:
        raise NotImplementedError

    async def count_unread(self, player_id: int) -> int:
        raise NotImplementedError


class NotificationMarker(Committer, Protocol):
    async def mark_read(self, player_id: int, notification_ids: Collection[int]) -> None:
        raise NotImplementedError

    async def mark_all_read(self, player_id: int) -> None:
        raise NotImplementedError


class NotificationWriter(Committer, Protocol):
    async def create(
        self,
        *,
        recipient_id: int,
        type_: NotificationType,
        severity: NotificationSeverity = ...,
        actor_id: int | None = ...,
        payload: dict[str, Any] | None = ...,
        request_id: int | None = ...,
    ) -> dto.Notification:
        raise NotImplementedError

    async def create_for_recipients(
        self,
        *,
        recipient_ids: Collection[int],
        type_: NotificationType,
        severity: NotificationSeverity = ...,
        actor_id: int | None = ...,
        payload: dict[str, Any] | None = ...,
        request_id: int | None = ...,
    ) -> None:
        raise NotImplementedError


class RequestNotifier(Protocol):
    async def notify_created(self, request: dto.ActionRequest) -> None:
        raise NotImplementedError


class RequestStorage(Committer, Protocol):
    async def create(
        self,
        *,
        type_: RequestType,
        initiator_id: int,
        target_player_id: int | None = ...,
        team_id: int | None = ...,
        game_id: int | None = ...,
        payload: dict[str, Any] | None = ...,
        expires_at: datetime | None = ...,
    ) -> dto.ActionRequest:
        raise NotImplementedError

    async def get_by_id(self, request_id: int) -> dto.ActionRequest:
        raise NotImplementedError

    async def get_pending(
        self,
        *,
        type_: RequestType,
        team_id: int | None = ...,
        game_id: int | None = ...,
        target_player_id: int | None = ...,
        initiator_id: int | None = ...,
    ) -> dto.ActionRequest | None:
        raise NotImplementedError

    async def set_status(
        self,
        request_id: int,
        status: RequestStatus,
        *,
        responder_id: int | None = ...,
    ) -> dto.ActionRequest:
        raise NotImplementedError

    async def get_incoming(
        self, player_id: int, *, only_pending: bool = ...
    ) -> Sequence[dto.ActionRequest]:
        raise NotImplementedError

    async def get_outgoing(
        self, player_id: int, *, only_pending: bool = ...
    ) -> Sequence[dto.ActionRequest]:
        raise NotImplementedError

    async def get_pending_for_teams(self, team_ids: Sequence[int]) -> Sequence[dto.ActionRequest]:
        raise NotImplementedError

    async def add_bot_message(self, request_id: int, *, chat_id: int, message_id: int) -> None:
        raise NotImplementedError

    async def get_bot_messages(self, request_id: int) -> Sequence[tuple[int, int]]:
        raise NotImplementedError
