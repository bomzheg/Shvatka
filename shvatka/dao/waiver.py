from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from shvatka.dao import BaseDAO
from shvatka.models import db, dto
from shvatka.models.enums.played import Played


class WaiverDao(BaseDAO[db.Waiver]):
    def __init__(self, session: AsyncSession):
        super().__init__(db.Waiver, session)

    async def is_excluded(
        self, game: dto.Game, player: dto.Player, team: dto.Team,
    ) -> bool:
        waiver = await self.get_or_none(game, player, team)
        if waiver is None:
            return False
        return waiver.played in (Played.revoked, Played.not_allowed)

    async def upsert(self, waiver: dto.Waiver):
        if waiver_db := await self.get_or_none(waiver.game, waiver.player, waiver.team):
            waiver_db.played = waiver.played
        else:
            waiver_db = db.Waiver(
                player_id=waiver.player.id,
                team_id=waiver.team.id,
                game_id=waiver.game.id,
                played=waiver.played,
            )
            self._save(waiver_db)
        await self._flush(waiver_db)

    async def delete(self, waiver: dto.Waiver):
        if waiver_db := await self.get_or_none(waiver.game, waiver.player, waiver.team):
            await self._delete(waiver_db)

    async def get_or_none(
        self, game: dto.Game, player: dto.Player, team: dto.Team,
    ) -> db.Waiver | None:
        result = await self.session.execute(
            select(self.model)
            .where(
                db.Waiver.team_id == team.id,
                db.Waiver.player_id == player.id,
                db.Waiver.game_id == game.id,
            )
        )
        return result.scalars().one_or_none()
