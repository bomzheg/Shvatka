from sqlalchemy.ext.asyncio import AsyncSession

from db import models
from .base import BaseDAO


class OrganizerDao(BaseDAO[models.Organizer]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.Organizer, session)
