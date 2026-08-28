from typing import Protocol

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.interfaces.dal.file_info import FileInfoGetter, GameFilesMetaGetter
from shvatka.core.interfaces.dal.game import (
    GameByIdGetter,
    GameNumberUpdater,
    GameReleaseGetter,
    GameRenamer,
    GameStatusCompleter,
    GameUpserter,
    MaxGameNumberGetter,
    WaiverStarter,
)
from shvatka.core.interfaces.dal.key_log import GameKeyGetter, TeamKeysMerger
from shvatka.core.interfaces.dal.level import MaxLevelNumberGetter
from shvatka.core.interfaces.dal.level_times import LevelTimesGetter, TeamLevelsMerger
from shvatka.core.interfaces.dal.organizer import OrgByPlayerGetter
from shvatka.core.interfaces.dal.player import TeamPlayersMerger
from shvatka.core.interfaces.dal.team import ForumTeamMerger, TeamRemover
from shvatka.core.interfaces.dal.waiver import GameWaiversGetter, WaiverMerger
from shvatka.core.models import dto


class TeamMerger(
    WaiverMerger,
    TeamKeysMerger,
    TeamLevelsMerger,
    TeamPlayersMerger,
    ForumTeamMerger,
    TeamRemover,
    Committer,
    Protocol,
):
    pass


class TypedKeyGetter(GameKeyGetter, OrgByPlayerGetter, Protocol):
    pass


class GameStatDao(
    OrgByPlayerGetter, LevelTimesGetter, MaxLevelNumberGetter, GameByIdGetter, Protocol
):
    pass


class GameCompleter(
    MaxGameNumberGetter, GameNumberUpdater, GameStatusCompleter, Committer, Protocol
):
    pass


class GameStatusChanger(GameByIdGetter, WaiverStarter, GameCompleter, GameReleaseGetter, Protocol):
    """Everything moving a game to its next status needs of storage.

    The release comes along because starting the waivers is what finally puts
    it in front of people.
    """


class GamePackager(
    GameKeyGetter,
    LevelTimesGetter,
    GameWaiversGetter,
    FileInfoGetter,
    GameFilesMetaGetter,
    Protocol,
):
    async def get_full(self, id_: int) -> dto.FullGame:
        raise NotImplementedError


class GameScenarioEditor(GameUpserter, GameRenamer, GameByIdGetter, FileInfoGetter, Protocol):
    pass
