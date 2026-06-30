from collections.abc import Collection
from datetime import datetime, tzinfo
import typing

from sqlalchemy import ScalarResult, select
from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.infrastructure.db import models
from .base import BaseDAO


class GameFileDao(BaseDAO[models.GameFile]):
    """DAO for the ``game_files`` m2m table (which files CAN be used in a game).

    Add-only: files registered here are never removed when a level is unlinked.
    """

    def __init__(
        self, session: AsyncSession, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        super().__init__(models.GameFile, session, clock=clock)

    async def get_file_ids(self, game_id: int) -> set[int]:
        result: ScalarResult[int] = await self.session.scalars(
            select(models.GameFile.file_id).where(models.GameFile.game_id == game_id)
        )
        return set(result.all())

    async def add_game_files(self, game_id: int, file_ids: Collection[int]) -> None:
        """Register files as usable in the game. Idempotent, never removes."""
        existing = await self.get_file_ids(game_id)
        for file_id in set(file_ids) - existing:
            self._save(models.GameFile(game_id=game_id, file_id=file_id))
