from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Body, Query, Response
from starlette import status

from shvatka.api.dependencies.auth import ApiIdentityProvider
from shvatka.api.models import req, responses
from shvatka.core.notifications.interactors import (
    ListNotificationsInteractor,
    UnreadCountInteractor,
    MarkNotificationsReadInteractor,
    MarkAllNotificationsReadInteractor,
)


@inject
async def get_notifications(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[ListNotificationsInteractor],
    unread: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> responses.Items[responses.Notification]:
    notifications = await interactor(
        identity=identity, unread_only=unread, limit=limit, offset=offset
    )
    return responses.Items([responses.Notification.from_core(n) for n in notifications])


@inject
async def get_unread_count(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[UnreadCountInteractor],
) -> responses.UnreadCount:
    return responses.UnreadCount(count=await interactor(identity=identity))


@inject
async def mark_read(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[MarkNotificationsReadInteractor],
    body: Annotated[req.MarkNotificationsRead, Body()],
) -> Response:
    await interactor(identity=identity, notification_ids=body.ids)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@inject
async def mark_all_read(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[MarkAllNotificationsReadInteractor],
) -> Response:
    await interactor(identity=identity)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def setup() -> APIRouter:
    router = APIRouter(prefix="/notifications", tags=["notifications"])
    router.add_api_route("", get_notifications, methods=["GET"])
    router.add_api_route("/unread-count", get_unread_count, methods=["GET"])
    router.add_api_route("/read", mark_read, methods=["POST"])
    router.add_api_route("/read-all", mark_all_read, methods=["PUT"])
    return router
