from datetime import datetime, tzinfo
import typing
from sqlalchemy import select, ScalarResult
from sqlalchemy import update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from shvatka.core.models import dto
from shvatka.core.models.dto.scn.level import LevelScenario
from shvatka.core.rules.game import check_game_editable
from shvatka.core.rules.level import check_can_link_to_game
from shvatka.infrastructure.db import models
from .base import BaseDAO


class LevelDao(BaseDAO[models.Level]):
    def __init__(
        self, session: AsyncSession, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        super().__init__(models.Level, session, clock=clock)

    async def upsert_gamed(
        self,
        author: dto.Player,
        scn: LevelScenario,
        game: dto.Game,
        no_in_game: int,
    ) -> dto.GamedLevel:
        level = await self.upsert(author, scn, game, no_in_game)
        return typing.cast(dto.GamedLevel, level)

    async def upsert(
        self,
        author: dto.Player,
        scn: LevelScenario,
        game: dto.Game | None = None,
        no_in_game: int | None = None,
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
        return await self._get_by_author_and_name_id(author, scn.id)

    async def _get_by_author_and_name_id(self, author: dto.Player, name_id: str) -> models.Level:
        result: ScalarResult[models.Level] = await self.session.scalars(
            select(models.Level)
            .options(joinedload(models.Level.game))
            .where(
                models.Level.name_id == name_id,
                models.Level.author_id == author.id,
            )
        )
        return result.one()

    async def get_by_author_and_name_id(
        self, author: dto.Player, name_id: str
    ) -> dto.Level | None:
        try:
            return (await self._get_by_author_and_name_id(author, name_id)).to_dto(author)
        except NoResultFound:
            return None

    async def get_all_my(self, author: dto.Player) -> list[dto.Level]:
        result: ScalarResult[models.Level] = await self.session.scalars(
            select(models.Level).where(models.Level.author_id == author.id)
        )
        levels = result.all()
        return [level.to_dto(author) for level in levels]

    async def get_by_id(self, id_: int) -> dto.Level:
        level = await self._get_by_id(
            id_,
            (
                joinedload(models.Level.author).joinedload(models.Player.user),
                joinedload(models.Level.author).joinedload(models.Player.forum_user),
            ),
        )
        return level.to_dto(level.author.to_dto_user_prefetched())

    async def unlink(self, level: dto.Level):
        await self.session.execute(
            update(models.Level).where(models.Level.id == level.db_id).values(game_id=None)
        )

    async def is_name_id_exist(self, name_id: str, author: dto.Player) -> bool:
        result = await self.session.scalars(
            select(models.Level.id).where(
                models.Level.name_id == name_id, models.Level.author_id == author.id
            )
        )
        return result.one_or_none() is not None

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

    async def link_to_game(self, level: dto.Level, game: dto.Game) -> dto.GamedLevel:
        max_level = await self.get_max_level_number(game)
        await self.session.execute(
            update(models.Level)
            .where(models.Level.id == level.db_id)
            .values(game_id=game.id, number_in_game=max_level + 1)
        )
        level.game_id = game.id
        level.number_in_game = max_level + 1
        return typing.cast(dto.GamedLevel, level)

    async def get_max_level_number(self, game: dto.Game) -> int:
        result = await self.session.execute(
            select(models.Level)
            .where(models.Level.game_id == game.id)
            .order_by(models.Level.number_in_game.desc())
            .limit(1)
        )
        max_level: models.Level | None = result.scalar_one_or_none()
        if max_level:
            return max_level.number_in_game
        return -1

    async def get_by_number(self, game: dto.Game, level_number: int) -> dto.GamedLevel:
        result = await self.session.execute(
            select(models.Level)
            .where(
                models.Level.game_id == game.id,
                models.Level.number_in_game == level_number,
            )
            .options(
                joinedload(models.Level.author).joinedload(models.Player.user),
                joinedload(models.Level.author).joinedload(models.Player.forum_user),
            )
        )
        level: models.Level = result.scalar_one()
        return level.to_gamed_dto(level.author.to_dto_user_prefetched())

    async def update_number_in_game(self, game_id: int) -> None:
        lvls: ScalarResult[models.Level] = await self.session.scalars(
            select(models.Level)
            .where(models.Level.game_id == game_id)
            .order_by(models.Level.number_in_game)
        )
        for i, lvl in enumerate(lvls.all()):
            lvl.number_in_game = i

    async def delete(self, level_id: int) -> None:
        _level = await self._get_by_id(level_id)
        await self.session.delete(_level)

    async def transfer(self, level: dto.Level, new_author: dto.Player):
        await self.session.execute(
            update(models.Level)
            .where(models.Level.id == level.db_id)
            .values(author_id=new_author.id)
        )

    async def transfer_all(self, primary: dto.Player, secondary: dto.Player):
        await self.session.execute(
            update(models.Level)
            .where(models.Level.author_id == secondary.id)
            .values(author_id=primary.id)
        )
