from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.dao import BaseDAO
from app.models import db, dto
from app.models.enums.played import Played


class WaiverDao(BaseDAO[db.Waiver]):
    def __init__(self, session: AsyncSession):
        super().__init__(db.Waiver, session)

    async def is_excluded(
        self, game: dto.Game, player: dto.Player, team: dto.Team,
    ) -> bool:
        result = await self.session.execute(
            select(self.model)
            .where(
                db.Waiver.team_id == team.id,
                db.Waiver.player_id == player.id,
                db.Waiver.game_id == game.id,
            )
        )
        try:
            waiver = result.scalar_one()
        except NoResultFound:
            return False
        return waiver.played in (Played.revoked, Played.not_allowed)
