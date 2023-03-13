from dataclasses import dataclass
from typing import Union, Any

from aiogram.filters import BaseFilter
from aiogram.types import Message

from shvatka.core.models import dto


@dataclass
class TeamPlayerFilter(BaseFilter):
    """if multiple values provided used AND semantic"""

    can_manage_waivers: bool | None = None
    can_manage_players: bool | None = None
    can_change_team_name: bool | None = None
    can_add_players: bool | None = None
    can_remove_players: bool | None = None
    is_captain: bool | None = None

    async def __call__(  # noqa: C901
        self,
        message: Message,
        team_player: dto.FullTeamPlayer,
    ) -> Union[bool, dict[str, Any]]:
        if self.is_captain is not None:
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
