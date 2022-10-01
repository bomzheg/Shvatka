from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.models import db
from .base import BaseDAO


class LevelTimeDao(BaseDAO[db.LevelTime]):
    def __init__(self, session: AsyncSession):
        super().__init__(db.LevelTime, session)
