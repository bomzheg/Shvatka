from sqlalchemy.ext.asyncio import AsyncSession

from db import models
from .base import BaseDAO


class LevelTimeDao(BaseDAO[models.LevelTime]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.LevelTime, session)
