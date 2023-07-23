from typing import Protocol

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.models import dto
from shvatka.core.models.dto import scn


class LevelUpserter(Committer, Protocol):
    async def upsert(
        self,
        author: dto.Player,
        scenario: scn.LevelScenario,
        game: dto.Game = None,
        no_in_game: int = None,
    ) -> dto.Level:
        raise NotImplementedError

    async def unlink_all(self, game: dto.Game) -> None:
        raise NotImplementedError


class MyLevelsGetter(Protocol):
    async def get_all_my(self, author: dto.Player) -> list[dto.Level]:
        raise NotImplementedError


class LevelByIdGetter(Protocol):
    async def get_by_id(self, id_: int) -> dto.Level:
        raise NotImplementedError


class LevelLinker(Committer, Protocol):
    async def link_to_game(self, level: dto.Level, game: dto.Game) -> dto.Level:
        raise NotImplementedError


class LevelAuthorMerger(Protocol):
    async def replace_levels_author(self, primary: dto.Player, secondary: dto.Player) -> None:
        raise NotImplementedError


class LevelUnlinker(Protocol):
    async def unlink(self, level: dto.Level) -> None:
        raise NotImplementedError


class LevelReorder(Protocol):
    async def update_number_in_game(self, game_id: int) -> None:
        raise NotImplementedError


class LevelDeleter(Committer, Protocol):
    async def delete(self, level_id: int) -> None:
        raise NotImplementedError


class LevelCorrectUnlinker(Committer, LevelUnlinker, LevelReorder, Protocol):
    pass
