import typing
from collections.abc import Sequence
from datetime import datetime, tzinfo
from typing import Any

from sqlalchemy import or_, select, ScalarResult
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.core.models.enums.request import RequestType, RequestStatus
from shvatka.core.notifications import dto
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.utils.exceptions import RequestNotFound
from shvatka.infrastructure.db.models import ActionRequest
from .base import BaseDAO


class ActionRequestDAO(BaseDAO[ActionRequest]):
    def __init__(
        self, session: AsyncSession, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        super().__init__(ActionRequest, session, clock=clock)

    async def create(
        self,
        *,
        type_: RequestType,
        initiator_id: int,
        target_player_id: int | None = None,
        team_id: int | None = None,
        game_id: int | None = None,
        payload: dict[str, Any] | None = None,
        expires_at: datetime | None = None,
    ) -> dto.ActionRequest:
        request = ActionRequest(
            type=type_.name,
            status=RequestStatus.pending,
            initiator_id=initiator_id,
            target_player_id=target_player_id,
            team_id=team_id,
            game_id=game_id,
            payload=payload or {},
            expires_at=expires_at,
        )
        self._save(request)
        await self._flush(request)
        return request.to_dto()

    async def get_by_id(self, request_id: int) -> dto.ActionRequest:
        try:
            request = await self._get_by_id(request_id)
        except NoResultFound as e:
            raise RequestNotFound(text=f"action request {request_id} not found") from e
        return request.to_dto()

    async def get_pending(
        self,
        *,
        type_: RequestType,
        team_id: int | None = None,
        game_id: int | None = None,
        target_player_id: int | None = None,
        initiator_id: int | None = None,
    ) -> dto.ActionRequest | None:
        stmt = select(ActionRequest).where(
            ActionRequest.type == type_.name,
            ActionRequest.status == RequestStatus.pending,
        )
        if team_id is not None:
            stmt = stmt.where(ActionRequest.team_id == team_id)
        if game_id is not None:
            stmt = stmt.where(ActionRequest.game_id == game_id)
        if target_player_id is not None:
            stmt = stmt.where(ActionRequest.target_player_id == target_player_id)
        if initiator_id is not None:
            stmt = stmt.where(ActionRequest.initiator_id == initiator_id)
        result = await self.session.scalars(stmt)
        found = result.first()
        return found.to_dto() if found is not None else None

    async def set_status(
        self,
        request_id: int,
        status: RequestStatus,
        *,
        responder_id: int | None = None,
    ) -> dto.ActionRequest:
        request = await self._get_by_id(request_id)
        request.status = status
        request.responder_id = responder_id
        request.responded_at = self.clock(tz_utc)
        await self._flush(request)
        return request.to_dto()

    async def get_incoming(
        self, player_id: int, *, only_pending: bool = False
    ) -> Sequence[dto.ActionRequest]:
        """Requests addressed to this player (as a named target)."""
        stmt = select(ActionRequest).where(ActionRequest.target_player_id == player_id)
        if only_pending:
            stmt = stmt.where(ActionRequest.status == RequestStatus.pending)
        stmt = stmt.order_by(ActionRequest.created_at.desc())
        result = await self.session.scalars(stmt)
        return [request.to_dto() for request in result.all()]

    async def get_outgoing(
        self, player_id: int, *, only_pending: bool = False
    ) -> Sequence[dto.ActionRequest]:
        """Requests this player initiated."""
        stmt = select(ActionRequest).where(ActionRequest.initiator_id == player_id)
        if only_pending:
            stmt = stmt.where(ActionRequest.status == RequestStatus.pending)
        stmt = stmt.order_by(ActionRequest.created_at.desc())
        result = await self.session.scalars(stmt)
        return [request.to_dto() for request in result.all()]

    async def add_bot_message(self, request_id: int, *, chat_id: int, message_id: int) -> None:
        request = await self._get_by_id(request_id)
        request.bot_messages = [
            *(request.bot_messages or []),
            {"chat_id": chat_id, "message_id": message_id},
        ]
        await self._flush(request)

    async def get_bot_messages(self, request_id: int) -> Sequence[tuple[int, int]]:
        result: ScalarResult[list[dict[str, int]]] = await self.session.scalars(
            select(ActionRequest.bot_messages).where(ActionRequest.id == request_id)
        )
        return [(d["chat_id"], d["message_id"]) for d in result.one()]

    async def get_pending_for_teams(self, team_ids: Sequence[int]) -> Sequence[dto.ActionRequest]:
        """Pending team-join requests answerable by managers of the given teams."""
        if not team_ids:
            return []
        stmt = select(ActionRequest).where(
            ActionRequest.type == RequestType.team_join_request.name,
            ActionRequest.status == RequestStatus.pending,
            or_(*[ActionRequest.team_id == team_id for team_id in team_ids]),
        )
        stmt = stmt.order_by(ActionRequest.created_at.desc())
        result = await self.session.scalars(stmt)
        return [request.to_dto() for request in result.all()]
