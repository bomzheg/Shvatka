from dishka import Provider, Scope, provide

from shvatka.core.games.interactors import (
    GameFileReaderInteractor,
    GamePlayReaderInteractor,
    GameKeysReaderInteractor,
    GameStatReaderInteractor,
    GamePlayTimerInteractor,
    CheckKeyInteractor,
)
from shvatka.core.games.adapters import (
    GameFileReader,
    GameKeysReader,
    GameStatReader,
    GamePlayDao,
)
from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.interfaces.dal.game import GameByIdGetter
from shvatka.core.interfaces.dal.game_play import GamePlayerDao
from shvatka.core.waiver.adapters import WaiverVoteAdder, WaiverVoteGetter
from shvatka.core.scenario.interactors import (
    AllGameKeysReaderInteractor,
    GameScenarioTransitionsInteractor,
)
from shvatka.core.services.current_game import CurrentGameProviderImpl
from shvatka.core.services.key import KeyProcessor, TimerProcessor
from shvatka.core.services.game_play import CheckKeyInteractor
from shvatka.core.waiver.interactors import WaiversReaderInteractor, AddWaiverVoteInteractor
from shvatka.infrastructure.db.dao.complex import WaiverVoteAdderImpl, WaiverVoteGetterImpl
from shvatka.infrastructure.db.dao.complex.game import GameFilesGetterImpl, GamePlayReaderImpl
from shvatka.infrastructure.db.dao.complex.game import (
    GameFilesGetterImpl,
    GamePlayDaoImpl,
)
from shvatka.infrastructure.db.dao.complex.game_play import GamePlayerDaoImpl
from shvatka.infrastructure.db.dao.complex.key_log import GameKeysReaderImpl
from shvatka.infrastructure.db.dao.complex.level_times import GameStatReaderImpl
from shvatka.infrastructure.db.dao.holder import HolderDao


class ContextProvider(Provider):
    scope = Scope.REQUEST
    current_game = provide(CurrentGameProviderImpl, provides=CurrentGameProvider)


class GamePlayProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_game_keys(self, dao: HolderDao) -> GameKeysReader:
        return GameKeysReaderImpl(dao)

    get_game_keys_interactor = provide(GameKeysReaderInteractor)

    @provide
    def get_game_state(self, dao: HolderDao) -> GameStatReader:
        return GameStatReaderImpl(dao)

    get_game_state_interactor = provide(GameStatReaderInteractor)

    @provide
    def get_game_files(self, dao: HolderDao) -> GameFileReader:
        return GameFilesGetterImpl(dao)

    file_reader = provide(GameFileReaderInteractor)
    game_play_reader_interactor = provide(GamePlayReaderInteractor)

    @provide
    def game_play_dao(self, dao: HolderDao, current_game: CurrentGameProvider) -> GamePlayDao:
        return GamePlayDaoImpl(dao=dao, current_game=current_game, cache={})

    @provide
    def game_player_dao(self, dao: HolderDao) -> GamePlayerDao:
        return GamePlayerDaoImpl(dao)

    check_key_interactor = provide(CheckKeyInteractor)
    key_processor = provide(KeyProcessor)
    timer_event_interactor = provide(GamePlayTimerInteractor)
    timer_processor = provide(TimerProcessor)

    @provide
    def game_by_id_getter(self, dao: HolderDao) -> GameByIdGetter:
        return dao.game

    all_game_keys_reader_interactor = provide(AllGameKeysReaderInteractor)
    transitions_reader_interactor = provide(GameScenarioTransitionsInteractor)


class WaiverProvider(Provider):
    scope = Scope.REQUEST

    waivers_reader_interactor = provide(WaiversReaderInteractor)
    add_waiver_vote = provide(AddWaiverVoteInteractor)

    waiver_vote_adder_dao = provide(WaiverVoteAdderImpl, provides=WaiverVoteAdder)
    waiver_vote_getter_dao = provide(WaiverVoteGetterImpl, provides=WaiverVoteGetter)
