from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.models import db
from .base import BaseDAO


class FileInfoDao(BaseDAO[db.FileInfo]):
    def __init__(self, session: AsyncSession):
        super().__init__(db.FileInfo, session)
