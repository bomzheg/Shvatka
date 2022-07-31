from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.dao import BaseDAO
from app.models import db, dto


class PlayerDao(BaseDAO[db.Player]):
    def __init__(self, session: AsyncSession):
        super().__init__(db.Player, session)

    async def upsert_player(self, user: dto.User) -> dto.Player:
        try:
            return await self.get_by_user(user)
        except NoResultFound:
            return await self.create_for_user(user)

    async def get_by_user(self, user: dto.User) -> dto.Player:
        result = await self.session.execute(
            select(db.Player).where(db.Player.user_id == user.db_id)
        )
        player = result.scalar_one()
        return dto.Player.from_db(player, user)

    async def create_for_user(self, user: dto.User) -> dto.Player:
        player = db.Player(
            user_id=user.db_id
        )
        self.session.add(player)
        await self.flush(player)
        return dto.Player.from_db(player, user)
