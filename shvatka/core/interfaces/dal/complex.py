from typing import Protocol

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.interfaces.dal.key_log import TeamKeysMerger
from shvatka.core.interfaces.dal.level_times import TeamLevelsMerger
from shvatka.core.interfaces.dal.player import TeamPlayerMerger
from shvatka.core.interfaces.dal.team import ForumTeamMerger, TeamRemover
from shvatka.core.interfaces.dal.waiver import WaiverMerger


class TeamMerger(
    WaiverMerger,
    TeamKeysMerger,
    TeamLevelsMerger,
    TeamPlayerMerger,
    ForumTeamMerger,
    TeamRemover,
    Committer,
    Protocol,
):
    pass