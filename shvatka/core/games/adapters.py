from collections.abc import Collection, Iterable
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
    GameRenamer,
    GameStartPlanner,
)
from shvatka.core.interfaces.dal.level_times import LevelByTeamGetter
from shvatka.core.interfaces.dal.player import PlayerByUserGetter
from shvatka.core.interfaces.dal.waiver import WaiverChecker
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.models.enums import GameStatus


class GameKeysReader(TypedKeyGetter, GameByIdGetter, PlayerByUserGetter, Protocol):
    pass


class GameNameEditor(GameByIdGetter, GameRenamer, Protocol):
    """Rename one game draft, addressed by its id.

    Narrower than :class:`~shvatka.core.interfaces.dal.complex.GameScenarioEditor`
    on purpose: the name is the one thing a game has before it has a scenario,
    so changing it must not need a scenario to be valid.
    """


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


class GameRuntimePurger(Protocol):
    """The per-table deletes that undo a game's run.

    Four tables hold what playing a game produces — ``levels_times``,
    ``log_keys``, ``event_log`` and ``timers_log`` — and each is dropped
    through its own table's dao. Nothing here decides *when*: the order the
    foreign keys demand (timers and keys, then events, then level times) is
    the use case's to walk, and ``timers_log`` has no game of its own, so its
    level time ids are resolved first and handed over.
    """

    async def get_level_time_ids(self, game: dto.Game) -> list[int]:
        raise NotImplementedError

    async def delete_timers(self, level_time_ids: Collection[int]) -> None:
        raise NotImplementedError

    async def delete_typed_keys(self, game: dto.Game) -> None:
        raise NotImplementedError

    async def delete_events(self, game: dto.Game) -> None:
        raise NotImplementedError

    async def delete_level_times(self, game: dto.Game) -> None:
        raise NotImplementedError


class AdminGameStatusChanger(
    GameByIdGetter, GameCompleter, GameStartPlanner, GameRuntimePurger, Protocol
):
    """Move a game between statuses on behalf of an admin, and list the ones
    the admin may act on.

    Deliberately narrow: it reads a game by id and writes its status (plus what
    completing one needs — the number — and what leaving the active statuses
    needs — cancelling the planned start). Nothing here reaches a level, a
    hint or a file, so the admin panel cannot read a game's content through it.

    The purge (``GameRuntimePurger``) is the one thing it reaches past the
    games table for, and it only *deletes*: sweeping the run of a game the
    admin is rewinding never reads a key, an event or where a team got to.
    """

    async def set_status(self, game: dto.Game, status: GameStatus) -> None:
        raise NotImplementedError

    async def get_by_statuses(self, statuses: Collection[GameStatus]) -> list[dto.Game]:
        raise NotImplementedError


class AdminLevelResender(LevelByTeamGetter, Protocol):
    """Resend a running level's messages to a team on behalf of an admin.

    As narrow as the job: who is playing the game, and since when each of them
    is on the level it is on. It reads no key, writes nothing, and the level
    itself comes from the game the caller already holds — so the panel gains
    no way to ask where a team is, only a way to send it what it should
    already have.
    """

    async def get_played_teams(self, game: dto.Game) -> Iterable[dto.Team]:
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
    pass


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
