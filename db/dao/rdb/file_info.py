from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db import models
from shvatka.models import dto
from shvatka.models.dto.scn import FileContent, SavedFileContent
from shvatka.utils.exceptions import PermissionsError
from .base import BaseDAO


class FileInfoDao(BaseDAO[models.FileInfo]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.FileInfo, session)

    async def upsert(self, file: FileContent, author: dto.Player) -> SavedFileContent:
        try:
            db_file = await self._get_by_guid(file.guid)
        except NoResultFound:
            db_file = models.FileInfo(guid=file.guid, author_id=author.id)
            self._save(db_file)
            await self._flush(db_file)
        db_file.file_path = file.file_content_link.file_path
        db_file.original_filename = file.original_filename
        db_file.extension = file.extension
        db_file.file_id = file.tg_link.file_id
        db_file.content_type = file.tg_link.content_type.name

        return db_file.to_dto(author=author)

    async def check_author_can_own_guid(self, author: dto.Player, guid: str) -> None:
        try:
            db_file = await self._get_by_guid(guid)
            if db_file.author_id != author.id:
                raise PermissionsError(notify_user="невозможно создать с таким guid")
        except NoResultFound:
            return


    async def _get_by_guid(self, guid: str) -> models.FileInfo:
        result = await self.session.execute(
            select(models.FileInfo)
            .where(models.FileInfo.guid == guid)
        )
        return result.scalar_one()
