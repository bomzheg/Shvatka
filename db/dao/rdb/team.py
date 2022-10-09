from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from db import models
from shvatka.models import dto
from shvatka.utils.exceptions import TeamError, AnotherTeamInChat
from .base import BaseDAO


class TeamDao(BaseDAO[models.Team]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.Team, session)

    async def create(self, chat: dto.Chat, captain: dto.Player) -> dto.Team:
        team = models.Team(
            chat_id=chat.db_id,
            captain_id=captain.id,
            name=chat.title,
            description=chat.description,
        )
        self.session.add(team)
        try:
            await self._flush(team)
        except IntegrityError as e:
            raise TeamError(
                chat=chat, player=captain, text="can't create team",
            ) from e
        return dto.Team(
            id=team.id,
            chat=chat,
            name=team.name,
            description=team.description,
            captain=captain,
        )

    async def get_by_chat(self, chat: dto.Chat) -> dto.Team | None:
        result = await self.session.execute(
            select(models.Team)
            .where(models.Team.chat_id == chat.db_id)
            .options(
                joinedload(models.Team.captain).joinedload(models.Player.user),
            )
        )
        try:
            team = result.scalar_one()
        except NoResultFound:
            return None
        return team.to_dto(chat)

    async def check_no_team_in_chat(self, chat: dto.Chat):
        if team := await self.get_by_chat(chat):
            raise AnotherTeamInChat(
                chat=chat, team=team, text="team in this chat exists",
            )

    async def get_by_id(self, id_: int):
        result = await self.session.execute(
            select(models.Team)
            .where(models.Team.id == id_)
            .options(
                joinedload(models.Team.captain).joinedload(models.Player.user),
                joinedload(models.Team.chat),
            )
        )
        team: models.Team = result.scalar_one()
        return team.to_dto(team.chat.to_dto())
