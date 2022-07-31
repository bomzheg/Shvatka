from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.dao import BaseDAO
from app.models import db, dto


class TeamDao(BaseDAO[db.Team]):
    def __init__(self, session: AsyncSession):
        super().__init__(db.Team, session)

    async def create(self, chat: dto.Chat, captain: dto.Player) -> dto.Team:
        team = db.Team(
            chat_id=chat.db_id,
            captain_id=captain.id,
            name=chat.title,
            description=None,
        )
        self.session.add(team)
        await self.flush(team)
        return dto.Team(
            id=team.id,
            chat=chat,
            name=team.name,
            description=team.description,
            captain=captain,
        )

    async def get_by_chat(self, chat: dto.Chat) -> dto.Team | None:
        try:
            result = await self.session.execute(
                select(db.Team)
                .where(db.Team.chat_id == chat.db_id)
                .options(
                    joinedload(db.Team.captain).joinedload(db.Player.user),
                )
            )
            team = result.scalar_one()
        except NoResultFound:
            return None
        return dto.Team(
            id=team.id,
            chat=chat,
            name=team.name,
            description=team.description,
            captain=dto.Player.from_db(
                player=team.captain, user=dto.User.from_db(team.captain.user),
            ),
        )
