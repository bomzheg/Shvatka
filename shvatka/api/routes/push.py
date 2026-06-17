from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Body, Header, Response
from starlette import status

from shvatka.api.config.models.main import ApiConfig
from shvatka.api.dependencies.auth import ApiIdentityProvider
from shvatka.api.models import req, responses
from shvatka.infrastructure.db.dao import PushSubscriptionDAO


@inject
async def get_push_config(config: FromDishka[ApiConfig]) -> responses.PushConfigResponse:
    return responses.PushConfigResponse(
        enabled=config.push.is_configured,
        public_key=config.push.vapid_public_key if config.push.is_configured else None,
    )


@inject
async def subscribe(
    identity: FromDishka[ApiIdentityProvider],
    dao: FromDishka[PushSubscriptionDAO],
    subscription: Annotated[req.PushSubscription, Body()],
    user_agent: Annotated[str | None, Header()] = None,
) -> Response:
    player = await identity.get_required_player()
    await dao.upsert(
        player_id=player.id,
        endpoint=subscription.endpoint,
        p256dh=subscription.keys.p256dh,
        auth=subscription.keys.auth,
        user_agent=user_agent,
    )
    await dao.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@inject
async def unsubscribe(
    identity: FromDishka[ApiIdentityProvider],
    dao: FromDishka[PushSubscriptionDAO],
    subscription: Annotated[req.PushSubscription, Body()],
) -> Response:
    player = await identity.get_required_player()
    await dao.delete_by_endpoint(
        player_id=player.id,
        endpoint=subscription.endpoint,
    )
    await dao.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def setup() -> APIRouter:
    router = APIRouter(prefix="/push", tags=["push"])
    router.add_api_route("/config", get_push_config, methods=["GET"])
    router.add_api_route("/subscriptions", subscribe, methods=["PUT"])
    router.add_api_route("/subscriptions", unsubscribe, methods=["DELETE"])
    return router
