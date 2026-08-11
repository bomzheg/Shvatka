from dataclasses import dataclass
from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import Message
from dishka import FromDishka
from dishka.integrations.aiogram import inject

from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.services.organizers import get_by_player_or_none
from shvatka.infrastructure.db.dao.holder import HolderDao


@dataclass
class OrgFilter(BaseFilter):
    """
    if multiple values provided used AND semantic,
    except is_primary (if provided - only this checked)
    and only_for_running_game
    """

    can_spy: bool | None = None
    can_see_log_keys: bool | None = None
    can_validate_waivers: bool | None = None
    is_primary: bool | None = None
    only_for_running_game: bool = True

    @inject
    async def __call__(  # noqa: C901
        self,
        message: Message,
        dao: HolderDao,
        identity: FromDishka[IdentityProvider],
        current_game: FromDishka[CurrentGameProvider],
    ) -> bool | dict[str, Any]:
        game = await current_game.get_game()
        if not game or not game.is_active():
            return False
        if self.only_for_running_game and not game.is_started():
            return False
        player = await identity.get_player()
        if player is None:
            return False
        org = await get_by_player_or_none(player=player, game=game, dao=dao.organizer)
        if org is None or org.deleted:
            return False
        if self.is_primary is not None:
            return isinstance(org, dto.PrimaryOrganizer)
        if self.can_spy is not None:
            if self.can_spy != org.can_spy:
                return False
        if self.can_see_log_keys is not None:
            if self.can_see_log_keys != org.can_see_log_keys:
                return False
        if self.can_validate_waivers is not None:
            if self.can_validate_waivers != org.can_validate_waivers:
                return False
        return {"org": org}
