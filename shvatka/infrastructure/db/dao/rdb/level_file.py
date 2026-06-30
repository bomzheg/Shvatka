from collections.abc import Collection
from datetime import datetime, tzinfo
import typing

from sqlalchemy import ScalarResult, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.infrastructure.db import models
from .base import BaseDAO


class LevelFileDao(BaseDAO[models.LevelFile]):
    """DAO for the ``level_files`` m2m table (which files a level references)."""

    def __init__(
        self, session: AsyncSession, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        super().__init__(models.LevelFile, session, clock=clock)

    async def get_file_ids(self, level_id: int) -> set[int]:
        result: ScalarResult[int] = await self.session.scalars(
            select(models.LevelFile.file_id).where(models.LevelFile.level_id == level_id)
        )
        return set(result.all())

    async def sync_level_files(self, level_id: int, file_ids: Collection[int]) -> None:
        """Make the level's file links match exactly ``file_ids``."""
        existing = await self.get_file_ids(level_id)
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

    async def delete_for_level(self, level_id: int) -> None:
        await self.session.execute(
            delete(models.LevelFile).where(models.LevelFile.level_id == level_id)
        )
