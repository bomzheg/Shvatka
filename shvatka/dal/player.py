from typing import Protocol

from shvatka.models import dto


class PlayerUpserter(Protocol):
    async def upsert_player(self, user: dto.User) -> dto.Player:
        pass

    async def commit(self) -> None:
        pass


class PlayerTeamChecker(Protocol):
    async def have_team(self, player: dto.Player) -> bool:
        pass

    async def get_team(self, player: dto.Player) -> dto.Team:
        pass

    async def get_player_in_team(self, player: dto.Player) -> dto.PlayerInTeam:
        pass


class PlayerPromoter(Protocol):
    async def promote(self, actor: dto.Player, target: dto.Player) -> None:
        pass

    async def commit(self) -> None:
        pass


class TeamJoiner(Protocol):
    async def join_team(self, player: dto.Player, team: dto.Team, role: str) -> None:
        pass

    async def commit(self) -> None:
        pass
