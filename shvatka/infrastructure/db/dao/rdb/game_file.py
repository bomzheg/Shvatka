from collections.abc import Collection
from datetime import datetime, tzinfo
import typing

from sqlalchemy import ScalarResult, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.core.files.dto import GameFileLink
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

    async def count_for_file(self, file_id: int) -> int:
        result = await self.session.execute(
            select(func.count(models.GameFile.id)).where(models.GameFile.file_id == file_id)
        )
        return result.scalar_one()

    async def get_unused_links(self) -> list[GameFileLink]:
        """Links to files no level of the same game refers to.

        Add-only means the table keeps a link after the hint that needed it is
        rewritten away, so this is where the leftovers show up. A file the
        game's release uses has no ``level_files`` row either — the caller
        decides what to do about that, this only reports the rows.
        """
        used_by_level = (
            select(models.LevelFile.id)
            .join(models.Level, models.Level.id == models.LevelFile.level_id)
            .where(
                models.Level.game_id == models.GameFile.game_id,
                models.LevelFile.file_id == models.GameFile.file_id,
            )
        )
        result = await self.session.execute(
            select(models.GameFile.id, models.GameFile.game_id, models.GameFile.file_id)
            .where(~used_by_level.exists())
            .order_by(models.GameFile.id)
        )
        return [
            GameFileLink(id=row.id, game_id=row.game_id, file_id=row.file_id) for row in result
        ]

    async def delete_link(self, game_id: int, file_id: int) -> None:
        await self.session.execute(
            delete(models.GameFile).where(
                models.GameFile.game_id == game_id,
                models.GameFile.file_id == file_id,
            )
        )

    async def delete_links(self, ids: Collection[int]) -> None:
        if not ids:
            return
        await self.session.execute(delete(models.GameFile).where(models.GameFile.id.in_(set(ids))))
