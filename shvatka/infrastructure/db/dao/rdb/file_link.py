from collections.abc import Collection
from datetime import datetime, tzinfo
import typing

from sqlalchemy import ScalarResult, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.infrastructure.db import models
from .base import BaseDAO


class FileLinkDao(BaseDAO[models.LevelFile]):
    """DAO for the file<->level and file<->game m2m tables.

    It only touches its own tables (``level_files`` / ``game_files``); resolving
    file guids to ids belongs to :class:`FileInfoDao`.
    """

    def __init__(
        self, session: AsyncSession, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        super().__init__(models.LevelFile, session, clock=clock)

    async def get_level_file_ids(self, level_id: int) -> set[int]:
        result: ScalarResult[int] = await self.session.scalars(
            select(models.LevelFile.file_id).where(models.LevelFile.level_id == level_id)
        )
        return set(result.all())

    async def get_game_file_ids(self, game_id: int) -> set[int]:
        result: ScalarResult[int] = await self.session.scalars(
            select(models.GameFile.file_id).where(models.GameFile.game_id == game_id)
        )
        return set(result.all())

    async def sync_level_files(self, level_id: int, file_ids: Collection[int]) -> None:
        """Make ``level_files`` match exactly the given files for the level."""
        existing = await self.get_level_file_ids(level_id)
        wanted = set(file_ids)
        for file_id in wanted - existing:
            self._save(models.LevelFile(level_id=level_id, file_id=file_id))
        to_remove = existing - wanted
        if to_remove:
            await self.session.execute(
                delete(models.LevelFile).where(
                    models.LevelFile.level_id == level_id,
                    models.LevelFile.file_id.in_(to_remove),
                )
            )

    async def add_game_files(self, game_id: int, file_ids: Collection[int]) -> None:
        """Register files as usable in the game. Idempotent, never removes."""
        existing = await self.get_game_file_ids(game_id)
        for file_id in set(file_ids) - existing:
            self._save(models.GameFile(game_id=game_id, file_id=file_id))
