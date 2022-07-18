from sqlalchemy.ext.asyncio import AsyncSession

from app.dao import BaseDAO
from app.models import db


class WaiverDao(BaseDAO[db.Waiver]):
    def __init__(self, session: AsyncSession):
        super().__init__(db.Waiver, session)
