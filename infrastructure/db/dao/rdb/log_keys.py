from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from infrastructure.db import models
from shvatka.models import dto
from shvatka.utils.datetime_utils import tz_utc
from .base import BaseDAO


class KeyTimeDao(BaseDAO[models.KeyTime]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.KeyTime, session)

    async def get_correct_typed_keys(
        self,
        level: dto.Level,
        game: dto.Game,
        team: dto.Team,
    ) -> set[str]:
        result = await self.session.scalars(
            select(models.KeyTime).where(
                models.KeyTime.game_id == game.id,
                models.KeyTime.level_number == level.number_in_game,
                models.KeyTime.team_id == team.id,
                models.KeyTime.is_correct.is_(True),  # noqa
            )
        )
        return {key.key_text for key in result.all()}

    async def is_duplicate(self, level: dto.Level, team: dto.Team, key: str) -> bool:
        result = await self.session.execute(
            select(self.model.id).where(
                models.KeyTime.game_id == level.game_id,
                models.KeyTime.level_number == level.number_in_game,
                models.KeyTime.team_id == team.id,
                models.KeyTime.key_text == key,
            )
        )
        return result.scalar() is not None

    async def save_key(
        self,
        key: str,
        team: dto.Team,
        level: dto.Level,
        game: dto.Game,
        player: dto.Player,
        is_correct: bool,
        is_duplicate: bool,
    ) -> dto.KeyTime:
        key_time = models.KeyTime(
            key_text=key,
            team_id=team.id,
            level_number=level.number_in_game,
            game_id=game.id,
            player_id=player.id,
            is_correct=is_correct,
            is_duplicate=is_duplicate,
            enter_time=datetime.now(tz=tz_utc),
        )
        self._save(key_time)
        return key_time.to_dto(player, team)

    async def get_typed_keys(self, game: dto.Game) -> list[dto.KeyTime]:
        result = await self.session.scalars(
            select(models.KeyTime)
            .where(models.KeyTime.game_id == game.id)
            .options(
                joinedload(models.KeyTime.team).joinedload(models.Team.chat),
                joinedload(models.KeyTime.player).joinedload(models.Player.user),
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
