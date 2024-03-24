from typing import Protocol

from shvatka.core.models import dto


class GameKeyGetter(Protocol):
    async def get_typed_keys_grouped(self, game: dto.Game) -> dict[dto.Team, list[dto.KeyTime]]:
        raise NotImplementedError


class GameTeamKeyGetter(Protocol):
    async def get_team_typed_keys(self, game: dto.Game, team: dto.Team) -> list[dto.KeyTime]:
        raise NotImplementedError


class TeamKeysMerger(Protocol):
    async def replace_team_keys(self, primary: dto.Team, secondary: dto.Team):
        raise NotImplementedError


class PlayerKeysMerger(Protocol):
    async def replace_player_keys(self, primary: dto.Player, secondary: dto.Player):
        raise NotImplementedError
