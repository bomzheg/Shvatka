from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db import models
from shvatka.models import dto
from shvatka.models.enums.played import Played
from .base import BaseDAO


class WaiverDao(BaseDAO[models.Waiver]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.Waiver, session)

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
            waiver_db = models.Waiver(
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
    ) -> models.Waiver | None:
        result = await self.session.execute(
            select(self.model)
            .where(
                models.Waiver.team_id == team.id,
                models.Waiver.player_id == player.id,
                models.Waiver.game_id == game.id,
            )
        )
        return result.scalars().one_or_none()
