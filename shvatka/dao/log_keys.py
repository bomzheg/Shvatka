from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.dao import BaseDAO
from shvatka.models import db


class KeyTimeDao(BaseDAO[db.KeyTime]):
    def __init__(self, session: AsyncSession):
        super().__init__(db.KeyTime, session)
