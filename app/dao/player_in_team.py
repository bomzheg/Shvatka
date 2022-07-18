from sqlalchemy.ext.asyncio import AsyncSession

from app.dao import BaseDAO
from app.models import db


class PlayerInTeamDao(BaseDAO[db.PlayerInTeam]):
    def __init__(self, session: AsyncSession):
        super().__init__(db.PlayerInTeam, session)
