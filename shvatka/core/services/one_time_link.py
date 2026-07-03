from dataclasses import dataclass

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.interfaces.one_time_token import OneTimeTokenCreator


@dataclass
class GenerateOneTimeLoginLinkInteractor:
    identity: IdentityProvider
    token_creator: OneTimeTokenCreator
    base_url: str

    async def __call__(self) -> str:
        player = await self.identity.get_required_player()
        token = await self.token_creator.save_new_token(dct={"player_id": player.id})
        return f"{self.base_url}/auth/one-time-token?token={token}"
