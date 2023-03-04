from typing import Iterable, Sequence

from sqlalchemy import select, Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.infrastructure.db import models
from src.core.models import dto
from src.core.models.enums.played import Played
from .base import BaseDAO


class WaiverDao(BaseDAO[models.Waiver]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.Waiver, session)

    async def is_excluded(
        self,
        game: dto.Game,
        player: dto.Player,
        team: dto.Team,
    ) -> bool:
        waiver = await self.get_or_none(game, player, team)
        if waiver is None:
            return False
        return waiver.played in (Played.revoked, Played.not_allowed)

    async def upsert_with_flush(self, waiver: dto.Waiver):
        waiver_db = await self._upsert(waiver)
        await self._flush(waiver_db)

    async def upsert(self, waiver: dto.Waiver):
        await self._upsert(waiver)

    async def _upsert(self, waiver: dto.Waiver) -> models.Waiver:
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
        return waiver_db

    async def delete(self, waiver: dto.Waiver):
        if waiver_db := await self.get_or_none(waiver.game, waiver.player, waiver.team):
            await self._delete(waiver_db)

    async def get_or_none(
        self,
        game: dto.Game,
        player: dto.Player,
        team: dto.Team,
    ) -> models.Waiver | None:
        result = await self.session.execute(
            select(self.model).where(
                models.Waiver.team_id == team.id,
                models.Waiver.player_id == player.id,
                models.Waiver.game_id == game.id,
            )
        )
        return result.scalars().one_or_none()

    async def get_played_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        result = await self.session.scalars(
            select(models.Waiver)
            .distinct(models.Waiver.team_id)  # Postgresql feature
            .options(
                joinedload(models.Waiver.team).joinedload(models.Team.chat),
                joinedload(models.Waiver.team).joinedload(models.Team.forum_team),
                joinedload(models.Waiver.team)
                .joinedload(models.Team.captain)
                .joinedload(models.Player.user),
                joinedload(models.Waiver.team)
                .joinedload(models.Team.captain)
                .joinedload(models.Player.forum_user),
            )
            .where(
                models.Waiver.game_id == game.id,
                models.Waiver.played == Played.yes,
            )
        )
        teams: Iterable[models.Team] = map(lambda w: w.team, result.all())
        return [team.to_dto_chat_prefetched() for team in teams]

    async def get_played(self, game: dto.Game, team: dto.Team) -> Iterable[dto.VotedPlayer]:
        result = await self.session.execute(
            select(models.Waiver, models.TeamPlayer)
            .options(
                joinedload(models.Waiver.player).joinedload(models.Player.user),
                joinedload(models.Waiver.player).joinedload(models.Player.forum_user),
            )
            .join(models.TeamPlayer, models.Waiver.player_id == models.TeamPlayer.player_id)
            .where(
                models.Waiver.game_id == game.id,
                models.Waiver.played == Played.yes,
                models.Waiver.team_id == team.id,
                models.TeamPlayer.date_left.is_(None),
            )
        )
        waivers: Sequence[Row[models.Waiver, models.TeamPlayer]] = result.all()
        return [
            dto.VotedPlayer(
                player=waiver.player.to_dto_user_prefetched(),
                pit=team_player.to_dto(),
            )
            for waiver, team_player in waivers
        ]
