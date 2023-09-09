from datetime import datetime
from typing import Sequence

from sqlalchemy import select, update, ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from shvatka.core.models import dto, enums
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db import models
from .base import BaseDAO


class KeyTimeDao(BaseDAO[models.KeyTime]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(models.KeyTime, session)

    async def get_correct_typed_keys(
        self,
        level: dto.Level,
        game: dto.Game,
        team: dto.Team,
    ) -> set[str]:
        result: ScalarResult[models.KeyTime] = await self.session.scalars(
            select(models.KeyTime).where(
                models.KeyTime.game_id == game.id,
                models.KeyTime.level_number == level.number_in_game,
                models.KeyTime.team_id == team.id,
                models.KeyTime.type_ == enums.KeyType.simple,
            )
        )
        return {key.key_text for key in result.all()}

    async def is_duplicate(self, level: dto.Level, team: dto.Team, key: str) -> bool:
        result: ScalarResult[int] = await self.session.scalars(
            select(self.model.id)
            .where(
                models.KeyTime.game_id == level.game_id,
                models.KeyTime.level_number == level.number_in_game,
                models.KeyTime.team_id == team.id,
                models.KeyTime.key_text == key,
            )
            .limit(1)
        )
        return result.one_or_none() is not None

    async def save_key(
        self,
        key: str,
        team: dto.Team,
        level: dto.Level,
        game: dto.Game,
        player: dto.Player,
        type_: enums.KeyType,
        is_duplicate: bool,
        at: datetime | None = None,
    ) -> dto.KeyTime:
        if at is None:
            at = datetime.now(tz=tz_utc)
        key_time = models.KeyTime(
            key_text=key,
            team_id=team.id,
            level_number=level.number_in_game,
            game_id=game.id,
            player_id=player.id,
            type_=type_,
            is_duplicate=is_duplicate,
            enter_time=at,
        )
        self._save(key_time)
        return key_time.to_dto(player, team)

    async def get_typed_keys(self, game: dto.Game) -> list[dto.KeyTime]:
        result = await self.session.scalars(
            select(models.KeyTime)
            .where(models.KeyTime.game_id == game.id)
            .options(
                joinedload(models.KeyTime.team).options(
                    joinedload(models.Team.chat),
                    joinedload(models.Team.forum_team),
                    joinedload(models.Team.captain).options(
                        joinedload(models.Player.user), joinedload(models.Player.forum_user)
                    ),
                ),
                joinedload(models.KeyTime.player).options(
                    joinedload(models.Player.user), joinedload(models.Player.forum_user)
                ),
            )
            .order_by(models.KeyTime.enter_time)
        )
        keys: Sequence[models.KeyTime] = result.all()
        return [
            key.to_dto(
                player=key.player.to_dto_user_prefetched(),
                team=key.team.to_dto_chat_prefetched(),
            )
            for key in keys
        ]

    async def get_typed_key_grouped(self, game: dto.Game) -> dict[dto.Team, list[dto.KeyTime]]:
        keys = await self.get_typed_keys(game)
        grouped: dict[dto.Team, list[dto.KeyTime]] = {}
        for key in keys:
            grouped.setdefault(key.team, []).append(key)
        return grouped

    async def replace_team_keys(self, primary: dto.Team, secondary: dto.Team):
        await self.session.execute(
            update(models.KeyTime)
            .where(models.KeyTime.team_id == secondary.id)
            .values(team_id=primary.id)
        )

    async def replace_player_keys(self, primary: dto.Player, secondary: dto.Player):
        await self.session.execute(
            update(models.KeyTime)
            .where(models.KeyTime.player_id == secondary.id)
            .values(player_id=primary.id)
        )
