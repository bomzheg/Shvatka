from datetime import date, datetime

from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.dao import BaseDAO
from app.models import db, dto
from app.utils.exceptions import PlayerAlreadyInTeam, PlayerRestoredInTeam


class PlayerInTeamDao(BaseDAO[db.PlayerInTeam]):
    def __init__(self, session: AsyncSession):
        super().__init__(db.PlayerInTeam, session)

    async def get_team(self, player: dto.Player) -> dto.Team | None:
        result = await self.session.execute(
            select(db.PlayerInTeam)
            .options(
                joinedload(db.PlayerInTeam.team)
                .joinedload(db.Team.captain)
                .joinedload(db.Player.user),
                joinedload(db.PlayerInTeam.team)
                .joinedload(db.Team.chat)
            )
            .where(
                db.PlayerInTeam.player_id == player.id,
                db.PlayerInTeam.date_left == None,  # noqa: E711
            )
        )
        try:
            player_in_team = result.scalar_one()
        except NoResultFound:
            return None
        team: db.Team = player_in_team.team
        return dto.Team.from_db(dto.Chat.from_db(team.chat), team)

    async def have_team(self, player: dto.Player) -> bool:
        return await self.get_team(player) is not None

    async def join_to_team(self, player: dto.Player, team: dto.Team, role: str):
        await self.check_player_free(player)
        if player_in_team := await self.need_restore(player, team):
            player_in_team.date_left = None
            await self.session.merge(player_in_team)
            raise PlayerRestoredInTeam(player=player, team=team)
        player_in_team = db.PlayerInTeam(
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

    async def need_restore(self, player: dto.Player, team: dto.Team) -> db.PlayerInTeam:
        result = await self.session.execute(
            select(db.PlayerInTeam)
            .where(
                db.PlayerInTeam.player_id == player.id,
                db.PlayerInTeam.date_left == date.today(),
                db.PlayerInTeam.team_id == team.id,
            )
        )
        return result.scalars().one_or_none()

    async def get_player_in_team(self, player: dto.Player) -> dto.PlayerInTeam:
        return dto.PlayerInTeam.from_db(await self._get_my_player_in_team(player))

    async def _get_my_player_in_team(self, player: dto.Player) -> db.PlayerInTeam:
        result = await self.session.execute(
            select(db.PlayerInTeam)
            .where(
                db.PlayerInTeam.player_id == player.id,
                db.PlayerInTeam.date_left == None,  # noqa: E711
            )
        )
        return result.scalar_one()
