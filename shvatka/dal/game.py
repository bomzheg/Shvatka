from abc import ABCMeta
from datetime import datetime

from shvatka.dal.base import Committer, Reader
from shvatka.dal.level import LevelUpserter
from shvatka.models import dto
from shvatka.models.dto.scn.game import GameScenario


class GameUpserter(LevelUpserter, metaclass=ABCMeta):
    async def upsert_game(self, author: dto.Player, scn: GameScenario) -> dto.Game:
        raise NotImplementedError


class GameCreator(Committer, metaclass=ABCMeta):
    async def create_game(self, author: dto.Player, name: str) -> dto.Game:
        raise NotImplementedError


class GameAuthorsFinder(Committer, metaclass=ABCMeta):
    async def get_all_by_author(self, author: dto.Player) -> list[dto.Game]:
        raise NotImplementedError


class GameByIdGetter(Committer, metaclass=ABCMeta):
    async def get_by_id(self, id_: int, author: dto.Player) -> dto.Game:
        raise NotImplementedError


class ActiveGameFinder(Reader):
    async def get_active_game(self) -> dto.Game | None:
        raise NotImplementedError


class WaiverStarter(Committer, ActiveGameFinder, metaclass=ABCMeta):
    async def start_waivers(self, game: dto.Game) -> None:
        raise NotImplementedError


class GameStartPlanner(Committer, ActiveGameFinder, metaclass=ABCMeta):
    async def set_start_at(self, game: dto.Game, start_at: datetime) -> None:
        raise NotImplementedError
