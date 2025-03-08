from datetime import datetime
from typing import Protocol

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.interfaces.dal.level import LevelUpserter
from shvatka.core.models import dto
from shvatka.core.models.dto import scn
from shvatka.core.models.dto import hints


class GameNameChecker(Protocol):
    async def is_name_available(self, name: str) -> bool:
        raise NotImplementedError


class MaxGameNumberGetter(Protocol):
    async def get_max_number(self) -> int:
        raise NotImplementedError


class GameNumberUpdater(Protocol):
    async def set_number(self, game: dto.Game, number: int) -> None:
        raise NotImplementedError


class GameStatusCompleter(Protocol):
    async def set_completed(self, game: dto.Game) -> None:
        raise NotImplementedError


class GameUpserter(LevelUpserter, GameNameChecker, Protocol):
    async def upsert_game(self, author: dto.Player, scenario: scn.GameScenario) -> dto.Game:
        raise NotImplementedError

    async def upsert_file(self, file: hints.FileMeta, author: dto.Player) -> hints.SavedFileMeta:
        raise NotImplementedError

    async def check_author_can_own_guid(self, author: dto.Player, guid: str) -> None:
        raise NotImplementedError

    async def is_author_game_by_name(self, name: str, author: dto.Player) -> bool:
        raise NotImplementedError

    async def get_game_by_name(self, name: str, author: dto.Player) -> dto.Game:
        raise NotImplementedError


class GameCreator(Committer, GameNameChecker, Protocol):
    async def create_game(self, author: dto.Player, name: str) -> dto.Game:
        raise NotImplementedError

    async def link_to_game(self, level: dto.Level, game: dto.Game) -> dto.Level:
        raise NotImplementedError


class GameRenamer(Committer, Protocol):
    async def rename_game(self, game: dto.Game, new_name: str):
        raise NotImplementedError


class GameAuthorsFinder(Committer, Protocol):
    async def get_all_by_author(self, author: dto.Player) -> list[dto.Game]:
        raise NotImplementedError


class PreviewGameByIdGetter(Protocol):
    async def get_preview(self, id_: int, author: dto.Player | None = None) -> dto.PreviewGame:
        raise NotImplementedError


class GameByIdGetter(Protocol):
    async def get_by_id(self, id_: int, author: dto.Player | None = None) -> dto.Game:
        raise NotImplementedError

    async def get_full(self, id_: int) -> dto.FullGame:
        raise NotImplementedError

    async def add_levels(self, game: dto.Game) -> dto.FullGame:
        raise NotImplementedError


class ActiveGameFinder(Protocol):
    async def get_active_game(self) -> dto.Game | None:
        raise NotImplementedError


class WaiverStarter(Committer, ActiveGameFinder, Protocol):
    async def start_waivers(self, game: dto.Game) -> None:
        raise NotImplementedError


class GameStartPlanner(Committer, ActiveGameFinder, Protocol):
    async def set_start_at(self, game: dto.Game, start_at: datetime) -> None:
        raise NotImplementedError

    async def cancel_start(self, game: dto.Game):
        raise NotImplementedError


class CompletedGameFinder(Protocol):
    async def get_completed_games(self) -> list[dto.Game]:
        raise NotImplementedError


class GameAuthorMerger(Protocol):
    async def replace_games_author(self, primary: dto.Player, secondary: dto.Player) -> None:
        raise NotImplementedError
