from dataclasses import dataclass

from .game import Game
from .player import Player


@dataclass(kw_only=True)
class Organizer:
    player: Player
    game: Game
    can_spy: bool
    can_see_log_keys: bool
    can_validate_waivers: bool
    deleted: bool

    @property
    def have_permissions(self) -> bool:
        return any(self._get_all_permissions())

    @property
    def have_disabled_permissions(self) -> bool:
        return not all(self._get_all_permissions())

    def _get_all_permissions(self) -> list[bool]:
        return [
            self.can_spy,
            self.can_see_log_keys,
            # self.can_validate_waivers,  # disabled, because no validate waivers logic present
        ]


@dataclass(kw_only=True)
class SecondaryOrganizer(Organizer):
    id: int


@dataclass(kw_only=True)
class PrimaryOrganizer(Organizer):
    can_spy: bool = True
    can_see_log_keys: bool = True
    can_validate_waivers: bool = True
    deleted: bool = False
