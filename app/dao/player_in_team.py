from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.dao import BaseDAO
from app.models import db, dto
from app.utils.exceptions import UserAlreadyInTeam


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

    async def add_in_team(self, player: dto.Player, team: dto.Team, role: str):
        if players_team := await self.get_team(player):
            raise UserAlreadyInTeam(
                player=player,
                team=players_team,
                text=f"user {player.id} already in team {players_team.id}",
            )
        player_in_team = db.PlayerInTeam(
            player_id=player.id,
            team_id=team.id,
            role=role,
        )
        self.session.add(player_in_team)
        await self.flush(player_in_team)
