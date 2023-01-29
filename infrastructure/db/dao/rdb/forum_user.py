from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db import models
from .base import BaseDAO


class ForumUserDAO(BaseDAO[models.ForumUser]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.ForumUser, session)
