from shvatka.dal.base import Committer
from shvatka.models import dto
from shvatka.models.dto.scn.level import LevelScenario


class LevelUpserter(Committer):
    async def upsert(
        self,
        author: dto.Player,
        scn: LevelScenario,
        game: dto.Game = None,
        no_in_game: int = None,
    ) -> None:
        pass

    async def unlink_all(self, game: dto.Game) -> None:
        pass
