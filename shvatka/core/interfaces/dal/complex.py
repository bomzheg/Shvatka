from typing import Protocol

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.interfaces.dal.game import MaxGameNumberGetter, GameNumberUpdater, GameStatusCompleter
from shvatka.core.interfaces.dal.key_log import TeamKeysMerger, GameKeyGetter
from shvatka.core.interfaces.dal.level_times import TeamLevelsMerger, LevelTimesGetter
from shvatka.core.interfaces.dal.organizer import OrgByPlayerGetter
from shvatka.core.interfaces.dal.player import TeamPlayersMerger
from shvatka.core.interfaces.dal.team import ForumTeamMerger, TeamRemover
from shvatka.core.interfaces.dal.waiver import WaiverMerger
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


class GameStatDao(OrgByPlayerGetter, LevelTimesGetter, Protocol):
    async def get_max_level_number(self, game: dto.Game) -> int:
        raise NotImplementedError


class GameCompleter(
    MaxGameNumberGetter, GameNumberUpdater, GameStatusCompleter, Committer, Protocol
):
    pass
