from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from db import models
from shvatka.models import dto
from .base import BaseDAO


class OrganizerDao(BaseDAO[models.Organizer]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.Organizer, session)

    async def get_orgs(self, game: dto.Game) -> Iterable[dto.Organizer]:
        return [dto.Organizer(
            id=None,
            player=game.author,
            game=game,
            can_spy=True,
            can_see_log_keys=True,
            can_validate_waivers=True,
            deleted=False
        )]

    async def get_orgs_count(self, game: dto.Game) -> int:
        return int(bool(game.author))
