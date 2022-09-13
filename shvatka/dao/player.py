from typing import Iterable

from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from shvatka.dao import BaseDAO
from shvatka.models import db, dto


class PlayerDao(BaseDAO[db.Player]):
    def __init__(self, session: AsyncSession):
        super().__init__(db.Player, session)

    async def upsert_player(self, user: dto.User) -> dto.Player:
        try:
            return await self.get_by_user(user)
        except NoResultFound:
            return await self.create_for_user(user)

    async def get_by_id(self, id_: int):
        player = await self.session.execute(
            select(db.Player)
            .where(db.Player.id == id_)
            .options(
                joinedload(db.Player.user, innerjoin=True)
            )
        )
        return dto.Player.from_db(player, dto.User.from_db(player.user))

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
        await self._flush(player)
        return dto.Player.from_db(player, user)

    async def promote(self, actor: dto.Player, target: dto.Player):
        target_player = await self._get_by_id(target.id)
        target_player.can_be_author = True
        target_player.promoted_by_id = actor.id

    async def get_by_ids_with_user_and_pit(self, ids: Iterable[int]) -> list[dto.VotedPlayer]:
        result = await self.session.execute(
            select(db.Player, db.PlayerInTeam)
            .options(
                joinedload(db.Player.user, innerjoin=True),
            )
            .join(db.Player.teams)
            .where(
                db.Player.id.in_(ids),
                db.PlayerInTeam.date_left.is_(None),  # noqa
            )
        )
        players = result.all()
        return [
            dto.VotedPlayer(
                dto.Player.from_db(player, dto.User.from_db(player.user)),
                dto.PlayerInTeam.from_db(pit),
            ) for player, pit in players
        ]
