from typing import Sequence

from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from infrastructure.db import models
from shvatka.models import dto
from shvatka.models.dto.scn.level import LevelScenario
from shvatka.services.game import check_game_editable
from shvatka.services.level import check_can_link_to_game
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
            level = await self._get_by_author_and_scn(author, scn)
        except NoResultFound:
            level = models.Level(
                author_id=author.id,
                name_id=scn.id,
            )
            self._save(level)
        else:
            if game_ := level.game:
                check_game_editable(game_.to_dto(author))
        level.scenario = scn
        if game is not None and no_in_game is not None:
            check_can_link_to_game(game, level.to_dto(author), author)
            level.game_id = game.id
            level.number_in_game = no_in_game
        await self._flush(level)
        return level.to_dto(author)

    async def _get_by_author_and_scn(self, author: dto.Player, scn: LevelScenario) -> models.Level:
        result = await self.session.execute(
            select(models.Level)
            .options(joinedload(models.Level.game))
            .where(
                models.Level.name_id == scn.id,
                models.Level.author_id == author.id,
            )
        )
        return result.scalar_one()

    async def get_all_my(self, author: dto.Player) -> list[dto.Level]:
        result = await self.session.scalars(
            select(models.Level).where(models.Level.author_id == author.id)
        )
        levels: Sequence[models.Level] = result.all()
        return [level.to_dto(author) for level in levels]

    async def get_by_id(self, id_: int) -> dto.Level:
        result = await self.session.execute(
            select(models.Level)
            .where(
                models.Level.id == id_,
            )
            .options(joinedload(models.Level.author).joinedload(models.Player.user))
        )
        level: models.Level = result.scalar_one()
        return level.to_dto(level.author.to_dto_user_prefetched())

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

    async def link_to_game(self, level: dto.Level, game: dto.Game) -> dto.Level:
        max_level = await self.get_max_level_number(game)
        await self.session.execute(
            update(models.Level)
            .where(models.Level.id == level.db_id)
            .values(game_id=game.id, number_in_game=max_level + 1)
        )
        level.game_id = game.id
        level.number_in_game = max_level + 1
        return level

    async def get_max_level_number(self, game: dto.Game) -> int:
        result = await self.session.execute(
            select(models.Level)
            .where(models.Level.game_id == game.id)
            .order_by(models.Level.number_in_game.desc())  # noqa
            .limit(1)
        )
        max_level: models.Level | None = result.scalar_one_or_none()
        if max_level:
            return max_level.number_in_game
        return -1

    async def get_by_number(self, game: dto.Game, level_number: int) -> dto.Level:
        result = await self.session.execute(
            select(models.Level)
            .where(
                models.Level.game_id == game.id,
                models.Level.number_in_game == level_number,
            )
            .options(joinedload(models.Level.author).joinedload(models.Player.user))
        )
        level: models.Level = result.scalar_one()
        return level.to_dto(level.author.to_dto_user_prefetched())

    async def transfer(self, level: dto.Level, new_author: dto.Player):
        await self.session.execute(
            update(models.Level)
            .where(models.Level.id == level.db_id)
            .values(author_id=new_author.id)
        )
