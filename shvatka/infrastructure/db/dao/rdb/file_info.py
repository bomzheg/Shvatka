from typing import Sequence

from sqlalchemy import select, ScalarResult
from sqlalchemy import update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from shvatka.core.models import dto
from shvatka.core.models.dto import scn
from shvatka.core.utils.exceptions import PermissionsError
from shvatka.infrastructure.db import models
from .base import BaseDAO


class FileInfoDao(BaseDAO[models.FileInfo]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.FileInfo, session)

    async def upsert(self, file: scn.FileMeta, author: dto.Player) -> scn.SavedFileMeta:
        try:
            db_file = await self._get_by_guid(file.guid)
        except NoResultFound:
            db_file = models.FileInfo(guid=file.guid, author_id=author.id)
            self._save(db_file)
            await self._flush(db_file)
        db_file.file_path = file.file_content_link.file_path
        db_file.original_filename = file.original_filename
        db_file.extension = file.extension
        if file.tg_link:
            db_file.file_id = file.tg_link.file_id
            db_file.content_type = file.tg_link.content_type.name
        if file.content_type:
            db_file.content_type = file.content_type.name

        return db_file.to_dto(author=author)

    async def check_author_can_own_guid(self, author: dto.Player, guid: str) -> None:
        try:
            db_file = await self._get_by_guid(guid)
            if db_file.author_id != author.id:
                raise PermissionsError(notify_user="невозможно создать с таким guid")
        except NoResultFound:
            return

    async def get_by_guid(self, guid: str) -> scn.VerifiableFileMeta:
        db_file = await self._get_by_guid(guid)
        return db_file.to_short_dto()

    async def transfer(self, file_guid: str, new_author: dto.Player):
        await self.session.execute(
            update(models.FileInfo)
            .where(models.FileInfo.guid == file_guid)
            .values(author_id=new_author.id)
        )

    async def transfer_all(self, primary: dto.Player, secondary: dto.Player) -> None:
        await self.session.execute(
            update(models.FileInfo)
            .where(models.FileInfo.author_id == secondary.id)
            .values(author_id=primary.id)
        )

    async def _get_by_guid(self, guid: str) -> models.FileInfo:
        result: ScalarResult[models.FileInfo] = await self.session.scalars(
            select(models.FileInfo).where(models.FileInfo.guid == guid)
        )
        return result.one()

    async def update_file_id(self, guid: str, file_id: str):
        await self.session.execute(
            update(models.FileInfo).where(models.FileInfo.guid == guid).values(file_id=file_id)
        )

    async def get_without_file_id(self, limit: int) -> Sequence[scn.SavedFileMeta]:
        result: ScalarResult[models.FileInfo] = await self.session.scalars(
            select(models.FileInfo)
            .where(models.FileInfo.file_id.is_(None))
            .options(
                joinedload(models.FileInfo.author).options(
                    joinedload(models.Player.user), joinedload(models.Player.forum_user)
                )
            )
            .limit(limit)
        )
        return [f.to_dto(f.author.to_dto_user_prefetched()) for f in result.all()]
