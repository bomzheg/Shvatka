from abc import ABCMeta
from typing import Iterable

from shvatka.dal.base import Writer, Committer
from shvatka.models import dto


class GamePreparer(Writer):
    async def delete_poll_data(self) -> None:
        raise NotImplementedError

    async def get_agree_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        raise NotImplementedError

    async def get_orgs(self, game: dto.Game) -> Iterable[dto.Organizer]:
        raise NotImplementedError


class KeyChecker(Committer, metaclass=ABCMeta):
    async def get_current_level(self, team: dto.Team, game: dto.Game) -> dto.Level:
        raise NotImplementedError

    async def get_correct_typed_keys(
        self, level: dto.Level, game: dto.Game, team: dto.Team,
    ) -> set[str]:
        raise NotImplementedError

    async def save_key(
        self, key: str, team: dto.Team, level: dto.Level, game: dto.Game,
        player: dto.Player, is_correct: bool,
    ) -> None:
        raise NotImplementedError

    async def level_up(self, team: dto.Team, level: dto.Level, game: dto.Game) -> None:
        raise NotImplementedError
