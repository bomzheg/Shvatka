from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db import models
from .base import BaseDAO


class ForumTeamDAO(BaseDAO[models.ForumTeam]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.ForumTeam, session)
