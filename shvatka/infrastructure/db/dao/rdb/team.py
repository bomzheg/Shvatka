import typing
from typing import Sequence

from sqlalchemy import select, ScalarResult
from sqlalchemy import update
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.interfaces import ORMOption

from shvatka.core.models import dto
from shvatka.core.utils.exceptions import TeamError, AnotherTeamInChat
from shvatka.infrastructure.db import models
from .base import BaseDAO


class TeamDao(BaseDAO[models.Team]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.Team, session)

    async def create(self, chat: dto.Chat, captain: dto.Player) -> dto.Team:
        chat_db = await self.session.get(models.Chat, chat.db_id)
        assert chat_db
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

    async def create_by_forum(self, forum: dto.ForumTeam, captain: dto.Player | None) -> dto.Team:
        forum_team_db = await self.session.get(models.ForumTeam, forum.id)
        assert forum_team_db
        if forum_team_db.team_id:
            team = await self._get_by_id(typing.cast(int, forum_team_db.team_id))
        else:
            team = models.Team(
                captain_id=captain.id if captain else None,
                name=forum.name,
                description=None,
                is_dummy=True,
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
        return team.to_dto(forum_team=forum, captain=captain)

    async def get_by_chat(self, chat: dto.Chat) -> dto.Team | None:
        result = await self.session.execute(
            select(models.Team)
            .join(models.Team.chat)
            .where(models.Chat.id == chat.db_id)
            .options(
                joinedload(models.Team.captain).options(
                    joinedload(models.Player.user),
                    joinedload(models.Player.forum_user),
                ),
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
            get_team_options(),
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
        result: ScalarResult[models.Team] = await self.session.scalars(
            select(models.Team)
            .join(models.Team.forum_team)
            .options(*get_team_options())
            .where(models.ForumTeam.name == name)
        )
        team = result.one()
        return team.to_dto_chat_prefetched()

    async def get_by_forum_team_id(self, forum_team_id: int) -> dto.Team:
        result: ScalarResult[models.Team] = await self.session.scalars(
            select(models.Team)
            .join(models.Team.forum_team)
            .options(*get_team_options())
            .where(models.ForumTeam.id == forum_team_id)
        )
        return result.one().to_dto_chat_prefetched()

    async def get_teams(self) -> list[dto.Team]:
        teams = await self._get_all(options=get_team_options())
        return [team.to_dto_chat_prefetched() for team in teams]

    async def get_played_games(self, team: dto.Team) -> list[dto.Game]:
        result = await self.session.scalars(
            select(models.Game)
            .distinct()
            .options(
                joinedload(models.Game.author).options(
                    joinedload(models.Player.user),
                    joinedload(models.Player.forum_user),
                ),
            )
            .join(models.Game.waivers)
            .where(
                models.Waiver.team_id == team.id,
                models.Game.number.is_not(None),
            )
            .order_by(models.Game.number)
        )
        games: Sequence[models.Game] = result.all()
        return [game.to_dto(game.author.to_dto_user_prefetched()) for game in games]

    async def delete(self, team: dto.Team):
        team_db = await self._get_by_id(team.id)
        await self.session.delete(team_db)


def get_team_options() -> Sequence[ORMOption]:
    return (
        joinedload(models.Team.captain).options(
            joinedload(models.Player.user),
            joinedload(models.Player.forum_user),
        ),
        joinedload(models.Team.chat),
        joinedload(models.Team.forum_team),
    )
