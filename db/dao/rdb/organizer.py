from typing import Iterable

from db import models
from shvatka.models import dto
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from .base import BaseDAO


class OrganizerDao(BaseDAO[models.Organizer]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.Organizer, session)

    async def get_orgs(self, game: dto.Game) -> Iterable[dto.SecondaryOrganizer]:
        orgs = await self._get_orgs(game)
        return [
            org.to_dto(
                player=org.player.to_dto(user=org.player.user.to_dto()),
                game=game,
            )
            for org in orgs
        ]

    async def get_orgs_count(self, game: dto.Game) -> int:
        return len(await self._get_orgs(game)) + 1

    async def _get_orgs(self, game: dto.Game) -> list[models.Organizer]:
        result = await self.session.execute(
            select(models.Organizer)
            .where(models.Organizer.game_id == game.id)
            .options(
                joinedload(models.Organizer.player)
                .joinedload(models.Player.user)
            )
        )
        return result.scalars().all()
