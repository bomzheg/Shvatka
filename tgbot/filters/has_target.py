from aiogram.filters import BaseFilter
from aiogram.types import Message

from shvatka.models import dto
from tgbot.username_resolver.find_target_user import get_target_user


class HasTargetFilter(BaseFilter):
    can_be_same: bool = False
    can_be_bot: bool = False

    async def __call__(self, message: Message) -> dict[str, dto.User]:
        target_user = get_target_user(message, self.can_be_same, self.can_be_bot)
        if target_user is None:
            return {}
        rez = {'target': target_user}
        return rez
