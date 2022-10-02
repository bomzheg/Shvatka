from datetime import datetime

from shvatka.dal.base import Committer, Reader
from shvatka.dal.level import LevelUpserter
from shvatka.models import dto
from shvatka.models.dto.scn.game import GameScenario


class GameUpserter(Committer, LevelUpserter):
    async def upsert_game(self, author: dto.Player, scn: GameScenario) -> dto.Game:
        pass


class GameCreator(Committer):
    async def create_game(self, author: dto.Player, name: str) -> dto.Game:
        pass


class GameAuthorsFinder(Committer):
    async def get_all_by_author(self, author: dto.Player) -> list[dto.Game]:
        pass


class GameByIdGetter(Committer):
    async def get_by_id(self, id_: int, author: dto.Player) -> dto.Game:
        pass


class ActiveGameFinder(Reader):
    async def get_active_game(self) -> dto.Game | None:
        pass


class WaiverStarter(Committer, ActiveGameFinder):
    async def start_waivers(self, game: dto.Game) -> None:
        pass


class GameStartPlanner(Committer, ActiveGameFinder):
    async def set_start_at(self, game: dto.Game, start_at: datetime) -> None:
        pass
