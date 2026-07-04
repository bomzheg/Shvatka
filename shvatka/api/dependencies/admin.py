import logging
from typing import NewType

from dishka import Provider, Scope, provide
from fastapi import HTTPException
from starlette import status

from shvatka.api.config.models.main import ApiConfig
from shvatka.api.dependencies.auth import ApiIdentityProvider
from shvatka.core.models import dto

logger = logging.getLogger(__name__)

# A player that has been authorised as a superuser (admin panel operator).
# Depending on it in a route enforces the admin check before the body runs.
Superuser = NewType("Superuser", dto.Player)


async def resolve_superuser(identity: ApiIdentityProvider, superusers: list[int]) -> dto.Player:
    player = await identity.get_required_player()
    user = await identity.get_user()
    if user is None or user.tg_id not in superusers:
        logger.info("player %s tried to access admin panel without rights", player.id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin rights required",
        )
    return player


class AdminProvider(Provider):
    scope = Scope.REQUEST

    @provide
    async def get_superuser(self, identity: ApiIdentityProvider, config: ApiConfig) -> Superuser:
        return Superuser(await resolve_superuser(identity, config.superusers))
