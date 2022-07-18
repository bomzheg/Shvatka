from sqlalchemy.ext.asyncio import AsyncSession

from app.dao import BaseDAO
from app.models import db


class LevelDao(BaseDAO[db.Level]):
    def __init__(self, session: AsyncSession):
        super().__init__(db.Level, session)
