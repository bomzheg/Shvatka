from datetime import datetime, timedelta

from sqlalchemy import update, not_
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from infrastructure.db import models
from shvatka.models import dto, enums
from shvatka.utils.datetime_utils import tz_utc
from shvatka.utils.exceptions import PlayerAlreadyInTeam, PlayerRestoredInTeam, PlayerNotInTeam
from .base import BaseDAO


class TeamPlayerDao(BaseDAO[models.TeamPlayer]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.TeamPlayer, session)

    async def get_team(self, player: dto.Player) -> dto.Team | None:
        result = await self.session.execute(
            select(models.TeamPlayer)
            .options(
                joinedload(models.TeamPlayer.team)
                .joinedload(models.Team.captain)
                .joinedload(models.Player.user),
                joinedload(models.TeamPlayer.team).joinedload(models.Team.chat),
            )
            .where(
                models.TeamPlayer.player_id == player.id,
                not_leaved(),
            )
        )
        try:
            team_player = result.scalar_one()
        except NoResultFound:
            return None
        team: models.Team = team_player.team
        return team.to_dto(team.chat.to_dto())

    async def have_team(self, player: dto.Player) -> bool:
        return await self.get_team(player) is not None

    async def join_team(
        self, player: dto.Player, team: dto.Team, role: str, as_captain: bool = False
    ):
        await self.check_player_free(player)
        if team_player := await self.need_restore(player, team):
            team_player.date_left = None
            await self.session.merge(team_player)
            raise PlayerRestoredInTeam(player=player, team=team)
        team_player = models.TeamPlayer(
            player_id=player.id,
            team_id=team.id,
            role=role,
        )
        if as_captain:
            team_player.can_remove_players = True
            team_player.can_manage_waivers = True
            team_player.can_add_players = True
            team_player.can_change_team_name = True
            team_player.can_manage_players = True
        self.session.add(team_player)
        await self._flush(team_player)

    async def leave_team(self, player: dto.Player):
        pit = await self._get_my_team_player(player)
        pit.date_left = datetime.now(tz=tz_utc)
        await self._flush(pit)

    async def check_player_free(self, player: dto.Player):
        if players_team := await self.get_team(player):
            raise PlayerAlreadyInTeam(
                player=player,
                team=players_team,
                text=f"user {player.id} already in team {players_team.id}",
            )

    async def need_restore(self, player: dto.Player, team: dto.Team) -> models.TeamPlayer:
        today = datetime.now(tz=tz_utc).date()
        result = await self.session.execute(
            select(models.TeamPlayer).where(
                models.TeamPlayer.player_id == player.id,
                models.TeamPlayer.date_left >= today,
                models.TeamPlayer.date_left < today + timedelta(days=1),
                models.TeamPlayer.team_id == team.id,
            )
        )
        return result.scalars().one_or_none()

    async def get_players(self, team: dto.Team) -> list[dto.FullTeamPlayer]:
        result = await self.session.execute(
            select(models.TeamPlayer)
            .where(
                models.TeamPlayer.team_id == team.id,
                not_leaved(),
            )
            .options(joinedload(models.TeamPlayer.player).joinedload(models.Player.user))
        )
        players: list[models.TeamPlayer] = result.scalars().all()
        return [
            dto.FullTeamPlayer.from_simple(
                team_player=team_player.to_dto(),
                player=team_player.player.to_dto_user_prefetched(),
                team=team,
            )
            for team_player in players
        ]

    async def get_team_player(self, player: dto.Player) -> dto.TeamPlayer:
        return (await self._get_my_team_player(player)).to_dto()

    async def flip_permission(
        self, player: dto.TeamPlayer, permission: enums.TeamPlayerPermission
    ):
        await self.session.execute(
            update(models.TeamPlayer)
            .where(models.TeamPlayer.id == player.id)
            .values(**{permission.name: not_(getattr(models.TeamPlayer, permission.name))})
        )

    async def _get_my_team_player(self, player: dto.Player) -> models.TeamPlayer:
        result = await self.session.execute(
            select(models.TeamPlayer).where(
                models.TeamPlayer.player_id == player.id,
                not_leaved(),
            )
        )
        try:
            return result.scalar_one()
        except NoResultFound:
            raise PlayerNotInTeam(player=player)


def not_leaved():
    # noinspection PyUnresolvedReferences
    return models.TeamPlayer.date_left.is_(None)  # noqa: E711
