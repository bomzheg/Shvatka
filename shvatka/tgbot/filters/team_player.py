from dataclasses import dataclass
from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import Message
from dishka import FromDishka
from dishka.integrations.aiogram import inject

from shvatka.core.interfaces.identity import IdentityProvider


@dataclass
class TeamPlayerFilter(BaseFilter):
    """if multiple values provided used AND semantic"""

    can_manage_waivers: bool | None = None
    can_manage_players: bool | None = None
    can_change_team_name: bool | None = None
    can_add_players: bool | None = None
    can_remove_players: bool | None = None
    is_captain: bool | None = None

    @inject
    async def __call__(  # noqa: C901
        self,
        message: Message,
        identity: FromDishka[IdentityProvider],
    ) -> bool | dict[str, Any]:
        team_player = await identity.get_full_team_player()
        if not team_player:
            return False
        if self.is_captain is not None:
            assert team_player.team.captain is not None
            return team_player.team.captain.id == team_player.player.id
        if self.can_manage_waivers is not None:
            if self.can_manage_waivers != team_player.can_manage_waivers:
                return False
        if self.can_manage_players is not None:
            if self.can_manage_players != team_player.can_manage_players:
                return False
        if self.can_change_team_name is not None:
            if self.can_change_team_name != team_player.can_change_team_name:
                return False
        if self.can_add_players is not None:
            if self.can_add_players != team_player.can_add_players:
                return False
        if self.can_remove_players is not None:
            if self.can_remove_players != team_player.can_remove_players:
                return False
        return True
