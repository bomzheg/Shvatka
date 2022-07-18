from sqlalchemy.ext.asyncio import AsyncSession

from app.dao import BaseDAO
from app.models import db


class TeamDao(BaseDAO[db.Team]):
    def __init__(self, session: AsyncSession):
        super().__init__(db.Team, session)
