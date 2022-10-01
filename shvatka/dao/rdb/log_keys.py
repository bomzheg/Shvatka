from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.models import db
from .base import BaseDAO


class KeyTimeDao(BaseDAO[db.KeyTime]):
    def __init__(self, session: AsyncSession):
        super().__init__(db.KeyTime, session)
