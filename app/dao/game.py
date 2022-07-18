from sqlalchemy.ext.asyncio import AsyncSession

from app.dao import BaseDAO
from app.models import db


class GameDao(BaseDAO[db.Game]):
    def __init__(self, session: AsyncSession):
        super().__init__(db.Game, session)
