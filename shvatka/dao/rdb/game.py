from datetime import datetime

from sqlalchemy import update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from shvatka.dal.game import ActiveGameFinder
from shvatka.models import db, dto
from shvatka.models.dto.scn.game import GameScenario
from shvatka.models.enums import GameStatus
from shvatka.models.enums.game_status import ACTIVE_STATUSES
from .base import BaseDAO


class GameDao(BaseDAO[db.Game], ActiveGameFinder):
    def __init__(self, session: AsyncSession):
        super().__init__(db.Game, session)

    async def upsert_game(
        self,
        author: dto.Player,
        scn: GameScenario,
    ) -> dto.Game:
        try:
            game = await self.get_by_author_and_scn(author, scn)
        except NoResultFound:
            game = db.Game(
                author_id=author.id,
                name=scn.name,
                status=GameStatus.underconstruction,
            )
            self._save(game)
        await self._flush(game)
        return dto.Game.from_db(game, author)

    async def get_by_author_and_scn(self, author: dto.Player, scn: GameScenario) -> db.Game:
        result = await self.session.execute(
            select(db.Game).where(
                db.Game.name == scn.name,
                db.Game.author_id == author.id,
            )
        )
        return result.scalar_one()

    async def get_by_id(self, id_: int, author: dto.Player) -> dto.Game:
        return dto.Game.from_db(await self._get_by_id(id_), author)

    async def get_all_by_author(self, author: dto.Player) -> list[dto.Game]:
        result = await self.session.execute(
            select(db.Game).where(
                db.Game.author_id == author.id,
                db.Game.status != GameStatus.complete,
            )
        )
        games = result.scalars().all()
        return [dto.Game.from_db(game, author) for game in games]

    async def start_waivers(self, game: dto.Game):
        await self.set_status(game, GameStatus.getting_waivers)

    async def start(self, game: dto.Game):
        await self.set_status(game, GameStatus.started)

    async def set_status(self, game: dto.Game, status: GameStatus):
        await self.session.execute(
            update(db.Game)
            .where(db.Game.id == game.id)
            .values(status=status)
        )

    async def get_active_game(self) -> dto.Game | None:
        result = await self.session.execute(
            select(db.Game)
            .where(db.Game.status.in_(ACTIVE_STATUSES))
            .options(
                joinedload(db.Game.author)
                .joinedload(db.Player.user)
            )
        )
        try:
            game: db.Game = result.scalar_one()
        except NoResultFound:
            return None
        return dto.Game.from_db(
            game, dto.Player.from_db(game.author, dto.User.from_db(game.author.user))
        )

    async def create_game(self, author: dto.Player, name: str) -> dto.Game:
        game_db = db.Game(
            author_id=author.id,
            name=name,
            status=GameStatus.underconstruction,
        )
        self._save(game_db)
        await self._flush(game_db)
        return dto.Game.from_db(game_db, author)

    async def set_start_at(self, game: dto.Game, start_at: datetime):
        await self.session.execute(
            update(db.Game)
            .where(db.Game.id == game.id)
            .values(start_at=start_at)
        )
