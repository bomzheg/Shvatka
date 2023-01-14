from typing import Iterable, Protocol

from shvatka.interfaces.dal.base import Committer
from shvatka.interfaces.dal.organizer import GameOrgsGetter
from shvatka.models import dto


class GamePreparer(Protocol, GameOrgsGetter):
    async def delete_poll_data(self) -> None:
        raise NotImplementedError

    async def get_agree_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        raise NotImplementedError

    async def get_poll_msg(self, team: dto.Team, game: dto.Game) -> int:
        raise NotImplementedError


class GamePlayerDao(Protocol, Committer, GameOrgsGetter):
    async def is_key_duplicate(self, level: dto.Level, team: dto.Team, key: str) -> bool:
        raise NotImplementedError

    async def get_played_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        raise NotImplementedError

    async def is_team_finished(self, team: dto.Team, game: dto.FullGame) -> bool:
        raise NotImplementedError

    async def is_all_team_finished(self, game: dto.FullGame) -> bool:
        raise NotImplementedError

    async def get_current_level(self, team: dto.Team, game: dto.Game) -> dto.Level:
        raise NotImplementedError

    async def get_correct_typed_keys(
        self,
        level: dto.Level,
        game: dto.Game,
        team: dto.Team,
    ) -> set[str]:
        raise NotImplementedError

    async def save_key(
        self,
        key: str,
        team: dto.Team,
        level: dto.Level,
        game: dto.Game,
        player: dto.Player,
        is_correct: bool,
        is_duplicate: bool,
    ) -> dto.KeyTime:
        raise NotImplementedError

    async def level_up(self, team: dto.Team, level: dto.Level, game: dto.Game) -> None:
        raise NotImplementedError

    async def finish(self, game: dto.Game) -> None:
        raise NotImplementedError

    async def get_current_level_time(self, team: dto.Team, game: dto.Game) -> dto.LevelTime:
        raise NotImplementedError
