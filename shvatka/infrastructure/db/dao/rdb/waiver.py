from typing import Iterable, Sequence

from sqlalchemy import select, Row, update, ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from shvatka.core.models import dto, enums
from shvatka.infrastructure.db import models
from .base import BaseDAO


class WaiverDao(BaseDAO[models.Waiver]):
    def __init__(self, session: AsyncSession) -> None:
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
        return waiver.played in (enums.Played.revoked, enums.Played.not_allowed)

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

    async def delete(self, waiver: dto.WaiverQuery):
        if waiver_db := await self.get_or_none(waiver.game, waiver.player, waiver.team):
            await self._delete(waiver_db)

    async def get_player_waiver(
        self,
        game: dto.Game,
        player: dto.Player,
        team: dto.Team,
    ) -> dto.Waiver | None:
        waiver_db = await self.get_or_none(game, player, team)
        if not waiver_db:
            return None
        return waiver_db.to_dto(player=player, team=team, game=game)

    async def get_or_none(
        self,
        game: dto.Game,
        player: dto.Player,
        team: dto.Team,
    ) -> models.Waiver | None:
        result: ScalarResult[models.Waiver] = await self.session.scalars(
            select(models.Waiver).where(
                models.Waiver.team_id == team.id,
                models.Waiver.player_id == player.id,
                models.Waiver.game_id == game.id,
            )
        )
        return result.one_or_none()

    async def get_all_by_game(self, game: dto.Game) -> list[dto.Waiver]:
        result: ScalarResult[models.Waiver] = await self.session.scalars(
            select(models.Waiver)
            .options(
                joinedload(models.Waiver.team).options(
                    joinedload(models.Team.chat),
                    joinedload(models.Team.forum_team),
                    joinedload(models.Team.captain).options(
                        joinedload(models.Player.user), joinedload(models.Player.forum_user)
                    ),
                ),
                joinedload(models.Waiver.player).options(
                    joinedload(models.Player.user), joinedload(models.Player.forum_user)
                ),
            )
            .where(models.Waiver.game_id == game.id)
        )
        return [
            w.to_dto(w.player.to_dto_user_prefetched(), w.team.to_dto_chat_prefetched(), game)
            for w in result.all()
        ]

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
                models.Waiver.played == enums.Played.yes,
            )
        )
        teams: Iterable[models.Team] = (w.team for w in result.all())
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
                models.Waiver.played == enums.Played.yes,
                models.Waiver.team_id == team.id,
                models.TeamPlayer.date_left.is_(None),
            )
        )
        waivers: Sequence[Row[tuple[models.Waiver, models.TeamPlayer]]] = result.all()
        return [
            dto.VotedPlayer(
                player=waiver.player.to_dto_user_prefetched(),
                pit=team_player.to_dto(),
            )
            for waiver, team_player in waivers
        ]

    async def replace_team_waiver(self, primary: dto.Team, secondary: dto.Team):
        await self.session.execute(
            update(models.Waiver)
            .where(models.Waiver.team_id == secondary.id)
            .values(team_id=primary.id)
        )

    async def is_team_played(self, team: dto.Team, game_number: int) -> bool:
        result = await self.session.scalars(
            select(models.Waiver.game_id)
            .distinct()
            .join(models.Waiver.game)
            .where(models.Waiver.team_id == team.id, models.Game.number == game_number)
        )
        return result.one_or_none() is not None

    async def is_player_played(self, player: dto.Player, game_number: int) -> bool:
        result = await self.session.scalars(
            select(models.Waiver.game_id)
            .distinct()
            .join(models.Waiver.game)
            .where(models.Waiver.player_id == player.id, models.Game.number == game_number)
        )
        return result.one_or_none() is not None

    async def replace_all_waivers(self, primary: dto.Player, secondary: dto.Player):
        await self.session.execute(
            update(models.Waiver)
            .where(models.Waiver.player_id == secondary.id)
            .values(player_id=primary.id)
        )

    async def check_waiver(self, player: dto.Player, team: dto.Team, game: dto.Game) -> bool:
        result: ScalarResult[models.Waiver] = await self.session.scalars(
            select(models.Waiver.id).where(
                models.Waiver.game_id == game.id,
                models.Waiver.team_id == team.id,
                models.Waiver.player_id == player.id,
                models.Waiver.played == enums.Played.yes,
            )
        )
        return bool(result.one_or_none())
