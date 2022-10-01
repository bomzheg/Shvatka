from sqlalchemy.ext.asyncio import AsyncSession

from db import models
from .base import BaseDAO


class KeyTimeDao(BaseDAO[models.KeyTime]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.KeyTime, session)
