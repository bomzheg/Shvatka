from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from infrastructure.db import models
from shvatka.models import dto
from shvatka.utils.exceptions import TeamError, AnotherTeamInChat
from .base import BaseDAO


class TeamDao(BaseDAO[models.Team]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.Team, session)

    async def create(self, chat: dto.Chat, captain: dto.Player) -> dto.Team:
        chat_db = await self.session.get(models.Chat, chat.db_id)
        team = models.Team(
            captain_id=captain.id,
            name=chat.title,
            description=chat.description,
        )
        chat_db.team = team
        self.session.add(team)
        try:
            await self._flush(team)
        except IntegrityError as e:
            raise TeamError(
                chat=chat,
                player=captain,
                text="can't create team",
            ) from e
        return dto.Team(
            id=team.id,
            chat=chat,
            name=team.name,
            description=team.description,
            captain=captain,
            is_dummy=team.is_dummy,
        )

    async def create_by_forum(self, forum: dto.ForumTeam, captain: dto.Player) -> dto.Team:
        forum_team_db = await self.session.get(models.ForumTeam, forum.id)
        team = models.Team(
            captain_id=captain.id if captain else None,
            name=forum.name,
            description=None,
        )
        forum_team_db.team = team
        self.session.add(team)
        try:
            await self._flush(team)
        except IntegrityError as e:
            raise TeamError(
                player=captain,
                text="can't create team",
            ) from e
        return dto.Team(
            id=team.id,
            chat=None,
            name=team.name,
            description=team.description,
            captain=captain,
            is_dummy=team.is_dummy,
        )

    async def get_by_chat(self, chat: dto.Chat) -> dto.Team | None:
        result = await self.session.execute(
            select(models.Team)
            .join(models.Team.chat)
            .where(models.Chat.id == chat.db_id)
            .options(
                joinedload(models.Team.captain).joinedload(models.Player.user),
                joinedload(models.Team.captain).joinedload(models.Player.forum_user),
            )
        )
        try:
            team = result.scalar_one()
        except NoResultFound:
            return None
        return team.to_dto(chat)

    async def check_no_team_in_chat(self, chat: dto.Chat) -> None:
        if team := await self.get_by_chat(chat):
            raise AnotherTeamInChat(
                chat=chat,
                team=team,
                text="team in this chat exists",
            )

    async def get_by_id(self, id_: int) -> dto.Team:
        team = await self._get_by_id(
            id_,
            (
                joinedload(models.Team.captain).joinedload(models.Player.user),
                joinedload(models.Team.captain).joinedload(models.Player.forum_user),
                joinedload(models.Team.chat),
                joinedload(models.Team.forum_team),
            ),
            populate_existing=True,
        )
        return team.to_dto_chat_prefetched()

    async def rename_team(self, team: dto.Team, new_name: str) -> None:
        await self.session.execute(
            update(models.Team).where(models.Team.id == team.id).values(name=new_name)
        )

    async def change_team_desc(self, team: dto.Team, new_desc: str) -> None:
        await self.session.execute(
            update(models.Team).where(models.Team.id == team.id).values(description=new_desc)
        )

    async def get_by_forum_team_name(self, name: str) -> dto.Team:
        result = await self.session.scalars(
            select(models.Team)
            .join(models.Team.forum_team)
            .options(
                joinedload(models.Team.captain).joinedload(models.Player.user),
                joinedload(models.Team.captain).joinedload(models.Player.forum_user),
                joinedload(models.Team.chat),
                joinedload(models.Team.forum_team),
            )
            .where(models.ForumTeam.name == name)
        )
        team: models.Team = result.one()
        return team.to_dto_chat_prefetched()
