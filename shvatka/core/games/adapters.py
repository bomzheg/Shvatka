from typing import Protocol

from shvatka.core.games.dto import CurrentHintsOnly, Event
from shvatka.core.interfaces.dal.complex import GameScenarioEditor, TypedKeyGetter, GameStatDao
from shvatka.core.interfaces.dal.file_info import FileInfoGetter
from shvatka.core.interfaces.dal.game import GameAuthorTransferer, GameByIdGetter
from shvatka.core.interfaces.dal.player import PlayerByUserGetter
from shvatka.core.interfaces.dal.waiver import WaiverChecker
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto


class GameKeysReader(TypedKeyGetter, GameByIdGetter, PlayerByUserGetter, Protocol):
    pass


class AdminGameScenarioEditor(GameScenarioEditor, GameAuthorTransferer, Protocol):
    """Edit a completed game's scenario on behalf of an admin.

    Extends the regular scenario editor with the ability to reassign the game's
    author (``transfer``) and its levels (``transfer_levels``), to resolve the
    target player by id (``get_player_by_id``) and to link a level to a game
    (``link_to_game``). ``PlayerByIdGetter.get_by_id`` is not composed in
    directly because it collides with ``GameByIdGetter.get_by_id``.
    """

    async def get_player_by_id(self, id_: int) -> dto.Player:
        raise NotImplementedError

    async def transfer_levels(self, game: dto.Game, new_author: dto.Player) -> None:
        raise NotImplementedError

    async def link_to_game(self, level: dto.Level, game: dto.Game) -> dto.GamedLevel:
        raise NotImplementedError


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
