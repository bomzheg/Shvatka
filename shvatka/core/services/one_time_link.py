import logging
from dataclasses import dataclass

from shvatka.core.interfaces.dal.player import PlayerByIdGetter
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.interfaces.one_time_token import OneTimeTokenCreator

logger = logging.getLogger(__name__)


@dataclass
class GenerateOneTimeLoginLinkInteractor:
    token_creator: OneTimeTokenCreator
    base_url: str

    async def __call__(self, identity: IdentityProvider) -> str:
        player = await identity.get_required_player()
        token = await self.token_creator.save_new_token(dct={"player_id": player.id})
        return f"{self.base_url}/auth/one-time-token?token={token}"


@dataclass
class GenerateOneTimeLoginLinkForPlayerInteractor:
    """Admin-panel variant: mint a one-time login link for an arbitrary player."""

    player_getter: PlayerByIdGetter
    token_creator: OneTimeTokenCreator
    base_url: str

    async def __call__(self, identity: IdentityProvider, player_id: int) -> str:
        admin = await identity.get_superuser()
        logger.warning("admin %s created a one-time login link for player %s", admin.id, player_id)
        player = await self.player_getter.get_by_id(player_id)
        token = await self.token_creator.save_new_token(dct={"player_id": player.id})
        return f"{self.base_url}/auth/one-time-token?token={token}"
