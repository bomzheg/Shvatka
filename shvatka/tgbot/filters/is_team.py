from dataclasses import dataclass

from aiogram.filters import BaseFilter
from dishka import FromDishka
from dishka.integrations.aiogram import inject

from shvatka.core.interfaces.identity import IdentityProvider


@dataclass
class IsTeamFilter(BaseFilter):
    is_team: bool = True

    @inject
    async def __call__(self, obj, identity: FromDishka[IdentityProvider]) -> bool:
        team = await identity.get_team()
        return (team is not None) == self.is_team
