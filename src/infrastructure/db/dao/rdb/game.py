from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy import update, func
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.core.models import dto
from src.core.models.dto.scn.game import GameScenario
from src.core.models.enums import GameStatus
from src.core.models.enums.game_status import ACTIVE_STATUSES
from src.core.utils.datetime_utils import tz_utc
from src.core.utils.exceptions import GameHasAnotherAuthor
from src.infrastructure.db import models
from .base import BaseDAO


class GameDao(BaseDAO[models.Game]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.Game, session)

    async def upsert_game(
        self,
        author: dto.Player,
        scn: GameScenario,
    ) -> dto.Game:
        try:
            game = await self._get_by_author_and_scn(author, scn)
        except NoResultFound:
            game = models.Game(
                author_id=author.id,
                name=scn.name,
                status=GameStatus.underconstruction,
            )
            self._save(game)
        await self._flush(game)
        return game.to_dto(author)

    async def _get_by_author_and_scn(self, author: dto.Player, scn: GameScenario) -> models.Game:
        result = await self.session.scalars(
            select(models.Game).where(
                models.Game.name == scn.name,
                models.Game.author_id == author.id,
            )
        )
        return result.one()

    async def get_full(self, id_: int) -> dto.FullGame:
        game_db = await self._get_by_id(
            id_,
            (
                joinedload(models.Game.levels),
                joinedload(models.Game.author).joinedload(models.Player.user),
                joinedload(models.Game.author).joinedload(models.Player.forum_user),
            ),
        )
        author = game_db.author.to_dto_user_prefetched()
        return game_db.to_full_dto(
            author=author,
            levels=[level.to_dto(author) for level in game_db.levels],
        )

    async def get_by_id(self, id_: int, author: dto.Player | None = None) -> dto.Game:
        if not author:
            options = (
                joinedload(models.Game.author).joinedload(models.Player.user),
                joinedload(models.Game.author).joinedload(models.Player.forum_user),
            )
            game = await self._get_by_id(id_, options)
            author = game.author.to_dto_user_prefetched()
        else:
            game = await self._get_by_id(id_)
            if author and game.author_id != author.id:
                raise GameHasAnotherAuthor(game_id=game.id, player=author)
        return game.to_dto(author)

    async def get_all_by_author(self, author: dto.Player) -> list[dto.Game]:
        result = await self.session.scalars(
            select(models.Game).where(
                models.Game.author_id == author.id,
                models.Game.status != GameStatus.complete,
            )
        )
        games = result.all()
        return [game.to_dto(author) for game in games]

    async def get_completed_games(self) -> list[dto.Game]:
        result = await self.session.scalars(
            select(models.Game)
            .options(
                joinedload(models.Game.author).joinedload(models.Player.user),
                joinedload(models.Game.author).joinedload(models.Player.forum_user),
            )
            .where(
                models.Game.status == GameStatus.complete,
            )
            .order_by(models.Game.number.desc(), models.Game.start_at.desc())  # noqa
        )
        games: Sequence[models.Game] = result.all()
        return [game.to_dto(game.author.to_dto_user_prefetched()) for game in games]

    async def start_waivers(self, game: dto.Game):
        await self.set_status(game, GameStatus.getting_waivers)

    async def start(self, game: dto.Game):
        await self.set_status(game, GameStatus.started)

    async def set_status(self, game: dto.Game, status: GameStatus):
        await self.session.execute(
            update(models.Game).where(models.Game.id == game.id).values(status=status)
        )
        game.status = status

    async def get_active_game(self) -> dto.Game | None:
        result = await self.session.scalars(
            select(models.Game)
            .where(models.Game.status.in_(ACTIVE_STATUSES))
            .options(
                joinedload(models.Game.author).joinedload(models.Player.user),
                joinedload(models.Game.author).joinedload(models.Player.forum_user),
            )
        )
        try:
            game: models.Game = result.one()
        except NoResultFound:
            return None
        return game.to_dto(game.author.to_dto_user_prefetched())

    async def create_game(self, author: dto.Player, name: str) -> dto.Game:
        game_db = models.Game(
            author_id=author.id,
            name=name,
            status=GameStatus.underconstruction,
        )
        self._save(game_db)
        await self._flush(game_db)
        return game_db.to_dto(author)

    async def set_start_at(self, game: dto.Game, start_at: datetime):
        await self.session.execute(
            update(models.Game)
            .where(models.Game.id == game.id)
            .values(start_at=start_at.astimezone(tz_utc))
        )

    async def cancel_start(self, game: dto.Game):
        await self.session.execute(
            update(models.Game).where(models.Game.id == game.id).values(start_at=None)
        )

    async def rename_game(self, game: dto.Game, new_name: str):
        await self.session.execute(
            update(models.Game).where(models.Game.id == game.id).values(name=new_name)
        )

    async def set_started(self, game: dto.Game):
        await self.set_status(game, GameStatus.started)

    async def set_finished(self, game: dto.Game):
        await self.set_status(game, GameStatus.finished)

    async def set_completed(self, game: dto.Game) -> None:
        await self.set_status(game, GameStatus.complete)

    async def set_published_channel_id(self, game: dto.Game, channel_id: int):
        await self.session.execute(
            update(models.Game)
            .where(models.Game.id == game.id)
            .values(published_channel_id=channel_id)
        )

    async def get_game_by_name(self, name: str, author: dto.Player) -> dto.Game:
        game = await self._get_game_by_name(name)
        return game.to_dto(author)

    async def transfer(self, game: dto.Game, new_author: dto.Player):
        await self.session.execute(
            update(models.Game).where(models.Game.id == game.id).values(author_id=new_author.id)
        )

    async def is_name_available(self, name: str) -> bool:
        return not bool(await self._get_game_by_name(name))

    async def set_number(self, game: dto.Game, number: int) -> None:
        await self.session.execute(
            update(models.Game).where(models.Game.id == game.id).values(number=number)
        )

    async def get_max_number(self) -> int:
        result = await self.session.scalar(select(func.max(models.Game.number)))
        return result or 0

    async def is_author_game_by_name(self, name: str, author: dto.Player) -> bool:
        result = await self._get_game_by_name(name)
        if result.author_id != author.id:
            return False
        return True

    async def _get_game_by_name(self, name: str) -> models.Game | None:
        result = await self.session.scalars(select(models.Game).where(models.Game.name == name))
        return result.one_or_none()
