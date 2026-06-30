from typing import Protocol

from shvatka.core.games.dto import CurrentHintsOnly, Event
from shvatka.core.interfaces.dal.complex import TypedKeyGetter, GameStatDao
from shvatka.core.interfaces.dal.file_info import FileInfoGetter
from shvatka.core.interfaces.dal.game import GameByIdGetter
from shvatka.core.interfaces.dal.player import PlayerByUserGetter
from shvatka.core.interfaces.dal.waiver import WaiverChecker
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto


class GameKeysReader(TypedKeyGetter, GameByIdGetter, PlayerByUserGetter, Protocol):
    pass


class GameStatReader(GameStatDao, GameByIdGetter, PlayerByUserGetter, Protocol):
    pass


class GameFileReader(FileInfoGetter, GameByIdGetter, PlayerByUserGetter, WaiverChecker, Protocol):
    async def is_game_file(self, game_id: int, guid: str) -> bool:
        """Whether the file is registered as usable in the game (game_files)."""
        raise NotImplementedError


class GamePlayDao(Protocol):
    async def get_current_hints(
        self,
        identity: IdentityProvider,
    ) -> CurrentHintsOnly:
        pass

    async def get_effects(
        self,
        identity: IdentityProvider,
    ) -> list[dto.GameEvent]:
        pass

    async def get_events(
        self,
        identity: IdentityProvider,
    ) -> list[Event]:
        pass

    async def get_team_typed_keys(
        self,
        identity: IdentityProvider,
    ) -> list[dto.InsertedKey]:
        pass

    async def check_waivers(self, identity: IdentityProvider) -> bool:
        pass
