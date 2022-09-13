from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.dao import BaseDAO
from shvatka.models import db


class FileInfoDao(BaseDAO[db.FileInfo]):
    def __init__(self, session: AsyncSession):
        super().__init__(db.FileInfo, session)
