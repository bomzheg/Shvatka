from sqlalchemy import update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db import models
from shvatka.models import dto
from shvatka.models.dto.scn.level import LevelScenario
from .base import BaseDAO


class LevelDao(BaseDAO[models.Level]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.Level, session)

    async def upsert(
        self,
        author: dto.Player,
        scn: LevelScenario,
        game: dto.Game = None,
        no_in_game: int = None,
    ) -> dto.Level:
        assert (game is None) == (no_in_game is None)
        try:
            level = await self.get_by_author_and_scn(author, scn)
        except NoResultFound:
            level = models.Level(
                author_id=author.id,
                name_id=scn.id,
            )
            self._save(level)
        level.scenario = scn
        if game is not None and no_in_game is not None:
            level.game_id = game.id
            level.number_in_game = no_in_game
        await self._flush(level)
        return dto.Level.from_db(level, author)

    async def get_by_author_and_scn(self, author: dto.Player, scn: LevelScenario) -> models.Level:
        result = await self.session.execute(
            select(models.Level).where(
                models.Level.name_id == scn.id,
                models.Level.author_id == author.id,
            )
        )
        return result.scalar_one()

    async def unlink_all(self, game: dto.Game):
        await self.session.execute(
            update(models.Level)
            .where(
                models.Level.game_id == game.id,
                models.Level.author_id == game.author.id,
            )
            .values(
                game_id=None,
                number_in_game=None,
            )
        )
