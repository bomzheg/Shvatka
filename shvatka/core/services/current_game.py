from typing import Iterable, TypedDict

from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.interfaces.dal.waiver import GameWaiversGetter
from shvatka.core.models import dto
from shvatka.core.waiver.services import get_all_played
from shvatka.infrastructure.db.dao import GameDao


class LoadedData(TypedDict, total=False):
    game: dto.Game | None
    full_game: dto.FullGame | None
    waivers: dict[dto.Team, Iterable[dto.VotedPlayer]]


class CurrentGameProviderImpl(CurrentGameProvider):
    def __init__(
        self,
        *,
        dao: GameDao,
        waiver_dao: GameWaiversGetter,
    ) -> None:
        self.dao = dao
        self.waiver_dao = waiver_dao
        self.cache = LoadedData()
        self.team_waivers_cache: dict[int, Iterable[dto.VotedPlayer]] = {}

    async def get_game(self) -> dto.Game | None:
        if "game" in self.cache:
            return self.cache["game"]
        game = await self.dao.get_active_game()

        self.cache["game"] = game
        return game

    async def get_full_game(self) -> dto.FullGame | None:
        if "full_game" in self.cache:
            return self.cache["full_game"]
        game = await self.get_game()
        if game is None:
            self.cache["full_game"] = None
            return None
        full_game = await self.dao.get_full(game.id)
        self.cache["full_game"] = full_game
        return full_game

    async def get_waivers(self) -> dict[dto.Team, Iterable[dto.VotedPlayer]]:
        if "waivers" in self.cache:
            return self.cache["waivers"]
        game = await self.get_required_game()
        waivers = await get_all_played(game, self.waiver_dao)
        self.cache["waivers"] = waivers
        return waivers

    async def get_team_waivers_by_team(self, team: dto.Team) -> Iterable[dto.VotedPlayer]:
        if team.id in self.team_waivers_cache:
            return self.team_waivers_cache[team.id]
        game = await self.get_required_game()
        players = await self.waiver_dao.get_played(game, team)
        self.team_waivers_cache[team.id] = players
        return players
