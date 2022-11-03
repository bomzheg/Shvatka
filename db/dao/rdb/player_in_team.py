from datetime import datetime, timedelta

from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from db import models
from shvatka.models import dto
from shvatka.utils.exceptions import PlayerAlreadyInTeam, PlayerRestoredInTeam
from .base import BaseDAO


class PlayerInTeamDao(BaseDAO[models.PlayerInTeam]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.PlayerInTeam, session)

    async def get_team(self, player: dto.Player) -> dto.Team | None:
        result = await self.session.execute(
            select(models.PlayerInTeam)
            .options(
                joinedload(models.PlayerInTeam.team)
                .joinedload(models.Team.captain)
                .joinedload(models.Player.user),
                joinedload(models.PlayerInTeam.team)
                .joinedload(models.Team.chat)
            )
            .where(
                models.PlayerInTeam.player_id == player.id,
                get_not_leaved_clause(),
            )
        )
        try:
            player_in_team = result.scalar_one()
        except NoResultFound:
            return None
        team: models.Team = player_in_team.team
        return team.to_dto(team.chat.to_dto())

    async def have_team(self, player: dto.Player) -> bool:
        return await self.get_team(player) is not None

    async def join_team(self, player: dto.Player, team: dto.Team, role: str):
        await self.check_player_free(player)
        if player_in_team := await self.need_restore(player, team):
            player_in_team.date_left = None
            await self.session.merge(player_in_team)
            raise PlayerRestoredInTeam(player=player, team=team)
        player_in_team = models.PlayerInTeam(
            player_id=player.id,
            team_id=team.id,
            role=role,
        )
        self.session.add(player_in_team)
        await self._flush(player_in_team)

    async def leave_team(self, player: dto.Player):
        pit = await self._get_my_player_in_team(player)
        pit.date_left = datetime.utcnow()
        await self._flush(pit)

    async def check_player_free(self, player: dto.Player):
        if players_team := await self.get_team(player):
            raise PlayerAlreadyInTeam(
                player=player,
                team=players_team,
                text=f"user {player.id} already in team {players_team.id}",
            )

    async def need_restore(self, player: dto.Player, team: dto.Team) -> models.PlayerInTeam:
        today = datetime.utcnow().date()
        result = await self.session.execute(
            select(models.PlayerInTeam)
            .where(
                models.PlayerInTeam.player_id == player.id,
                models.PlayerInTeam.date_left >= today,
                models.PlayerInTeam.date_left < today + timedelta(days=1),
                models.PlayerInTeam.team_id == team.id,
            )
        )
        return result.scalars().one_or_none()

    async def get_player_in_team(self, player: dto.Player) -> dto.PlayerInTeam:
        return (await self._get_my_player_in_team(player)).to_dto()

    async def _get_my_player_in_team(self, player: dto.Player) -> models.PlayerInTeam:
        result = await self.session.execute(
            select(models.PlayerInTeam)
            .where(
                models.PlayerInTeam.player_id == player.id,
                get_not_leaved_clause(),
            )
        )
        return result.scalar_one()


def get_not_leaved_clause():
    # noinspection PyUnresolvedReferences
    return models.PlayerInTeam.date_left.is_(None)  # noqa: E711
