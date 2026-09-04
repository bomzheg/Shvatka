import typing
from collections.abc import Collection
from datetime import datetime, tzinfo

from sqlalchemy import ScalarResult, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.infrastructure.db import models

from .base import BaseDAO


class LevelFileDao(BaseDAO[models.LevelFile]):
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

    async def get_level_ids_by_file(self, game_id: int, file_id: int) -> set[int]:
        result: ScalarResult[int] = await self.session.scalars(
            select(models.LevelFile.level_id)
            .join(models.Level, models.Level.id == models.LevelFile.level_id)
            .where(models.Level.game_id == game_id, models.LevelFile.file_id == file_id)
        )
        return set(result.all())

    async def count_for_file(self, file_id: int) -> int:
        result = await self.session.execute(
            select(func.count(models.LevelFile.id)).where(models.LevelFile.file_id == file_id)
        )
        return result.scalar_one()
