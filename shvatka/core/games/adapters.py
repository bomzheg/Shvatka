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
    pass


class AdminGameScenarioEditor(GameScenarioEditor, GameAuthorTransferer, Protocol):
    async def get_player_by_id(self, id_: int) -> dto.Player:
        raise NotImplementedError

    async def transfer_levels(self, game: dto.Game, new_author: dto.Player) -> None:
        raise NotImplementedError

    async def link_to_game(self, level: dto.Level, game: dto.Game) -> dto.GamedLevel:
        raise NotImplementedError


class GameRuntimePurger(Protocol):
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
    async def set_status(self, game: dto.Game, status: GameStatus) -> None:
        raise NotImplementedError

    async def get_by_statuses(self, statuses: Collection[GameStatus]) -> list[dto.Game]:
        raise NotImplementedError


class AdminLevelResender(LevelByTeamGetter, Protocol):
    async def get_played_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        raise NotImplementedError


class GameBonusesGetter(Protocol):
    async def get_game_bonuses_by_teams(self, game: dto.Game) -> dict[int, list[BonusEvent]]:
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
