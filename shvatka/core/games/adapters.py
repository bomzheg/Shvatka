from typing import Protocol

from shvatka.core.interfaces.dal.complex import TypedKeyGetter
from shvatka.core.interfaces.dal.file_info import FileInfoGetter
from shvatka.core.interfaces.dal.game import GameByIdGetter, ActiveGameFinder
from shvatka.core.interfaces.dal.key_log import GameTeamKeyGetter
from shvatka.core.interfaces.dal.level import LevelByGameAndNumberGetter
from shvatka.core.interfaces.dal.level_times import LevelByTeamGetter
from shvatka.core.interfaces.dal.player import PlayerByUserGetter, TeamByPlayerGetter
from shvatka.core.interfaces.dal.waiver import WaiverChecker


class GameKeysReader(TypedKeyGetter, GameByIdGetter, PlayerByUserGetter, Protocol):
    pass


class GameFileReader(FileInfoGetter, GameByIdGetter, PlayerByUserGetter, Protocol):
    pass


class GamePlayReader(
    ActiveGameFinder,
    PlayerByUserGetter,
    TeamByPlayerGetter,
    WaiverChecker,
    LevelByTeamGetter,
    LevelByGameAndNumberGetter,
    GameTeamKeyGetter,
    Protocol,
):
    pass
