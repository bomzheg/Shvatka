from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.models import db
from .base import BaseDAO


class OrganizerDao(BaseDAO[db.Organizer]):
    def __init__(self, session: AsyncSession):
        super().__init__(db.Organizer, session)
