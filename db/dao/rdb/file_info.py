from sqlalchemy.ext.asyncio import AsyncSession

from db import models
from .base import BaseDAO


class FileInfoDao(BaseDAO[models.FileInfo]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.FileInfo, session)
