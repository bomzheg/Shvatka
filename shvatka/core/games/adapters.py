from collections.abc import Collection
from typing import Protocol

from shvatka.core.games.dto import BonusEvent, CurrentHintsOnly, Event, PassedLevels
from shvatka.core.interfaces.dal.complex import (
    GameCompleter,
    GameScenarioEditor,
    GameStatDao,
    TypedKeyGetter,
)
from shvatka.core.interfaces.dal.file_info import FileInfoGetter
from shvatka.core.interfaces.dal.file_link import FileIdsByGuidsGetter, GameFilesAdder
from shvatka.core.interfaces.dal.game import (
    GameAuthorTransferer,
    GameByIdGetter,
    GameReleaseGetter,
    GameReleaseSaver,
    GameStartPlanner,
)
from shvatka.core.interfaces.dal.player import PlayerByUserGetter
from shvatka.core.interfaces.dal.waiver import WaiverChecker
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.models.enums import GameStatus


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


class AdminGameStatusChanger(GameByIdGetter, GameCompleter, GameStartPlanner, Protocol):
    """Move a game between statuses on behalf of an admin, and list the ones
    the admin may act on.

    Deliberately narrow: it reads a game by id and writes its status (plus what
    completing one needs — the number — and what leaving the active statuses
    needs — cancelling the planned start). Nothing here reaches a level, a
    hint or a file, so the admin panel cannot read a game's content through it.
    """

    async def set_status(self, game: dto.Game, status: GameStatus) -> None:
        raise NotImplementedError

    async def get_by_statuses(self, statuses: Collection[GameStatus]) -> list[dto.Game]:
        raise NotImplementedError


class GameBonusesGetter(Protocol):
    async def get_game_bonuses_by_teams(self, game: dto.Game) -> dict[int, list[BonusEvent]]:
        """All teams' bonuses and penalties for the game, grouped by team id."""
        raise NotImplementedError


class GameStatReader(GameStatDao, GameBonusesGetter, GameByIdGetter, PlayerByUserGetter, Protocol):
    pass


class GameFileReader(
    FileInfoGetter,
    GameByIdGetter,
    GameReleaseGetter,
    PlayerByUserGetter,
    WaiverChecker,
    Protocol,
):
    async def is_game_file(self, game_id: int, guid: str) -> bool:
        """Whether the file is registered as usable in the game (game_files)."""
        raise NotImplementedError


class GameReleaseReader(GameByIdGetter, GameReleaseGetter, Protocol):
    """Reads a game's announcement (and the game it belongs to)."""


class GameReleaseEditor(
    GameByIdGetter,
    GameReleaseSaver,
    FileIdsByGuidsGetter,
    GameFilesAdder,
    Protocol,
):
    """Writes a game's announcement, registering the files it references.

    A release may reference files the author uploaded straight into the
    announcement (that's how the bot works), so saving it also makes them
    usable in the game — otherwise the banner couldn't be served from the cdn
    endpoint.
    """

    async def check_author_can_own_guid(self, author: dto.Player, guid: str) -> None:
        raise NotImplementedError


class GamePlayDao(Protocol):
    async def get_current_hints(
        self,
        identity: IdentityProvider,
    ) -> CurrentHintsOnly:
        pass

    async def get_passed_levels(
        self,
        identity: IdentityProvider,
    ) -> PassedLevels:
        """Levels the team has already left, with the hints it saw on each."""

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
