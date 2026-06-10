from typing import Iterable, Protocol

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.utils import exceptions


class CurrentGameProvider(Protocol):
    async def get_game(self) -> dto.Game | None:
        raise NotImplementedError

    async def get_required_game(self) -> dto.Game:
        game = await self.get_game()
        if game is None:
            raise exceptions.HaveNotActiveGame
        return game

    async def get_full_game(self) -> dto.FullGame | None:
        raise NotImplementedError

    async def get_required_full_game(self) -> dto.FullGame:
        full_game = await self.get_full_game()
        if full_game is None:
            raise exceptions.HaveNotActiveGame
        return full_game

    async def get_waivers(self) -> dict[dto.Team, Iterable[dto.VotedPlayer]]:
        """All teams (with players) which voted yes for the current game."""
        raise NotImplementedError

    async def get_team_waivers_by_team(self, team: dto.Team) -> Iterable[dto.VotedPlayer]:
        """Players of the identity's team which voted yes for the current game."""
        raise NotImplementedError

    async def get_team_waivers(self, identity: IdentityProvider) -> Iterable[dto.VotedPlayer]:
        return await self.get_team_waivers_by_team(await identity.get_required_team())

    async def is_player_played(self, identity: IdentityProvider) -> bool:
        player = await identity.get_required_player()
        return any(voted.player.id == player.id for voted in await self.get_team_waivers(identity))

    async def is_team_played(self, identity: IdentityProvider) -> bool:
        return any(True for _ in await self.get_team_waivers(identity))
