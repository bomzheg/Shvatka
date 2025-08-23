from dishka import Provider, Scope, provide

from shvatka.core.games.interactors import (
    GameFileReaderInteractor,
    GamePlayReaderInteractor,
    GameKeysReaderInteractor,
    GameStatReaderInteractor,
)
from shvatka.core.games.adapters import (
    GameFileReader,
    GamePlayReader,
    GameKeysReader,
    GameStatReader,
)
from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.interfaces.dal.game import GameByIdGetter
from shvatka.core.interfaces.dal.game_play import GamePlayerDao
from shvatka.core.scenario.interactors import (
    AllGameKeysReaderInteractor,
    GameScenarioTransitionsInteractor,
)
from shvatka.core.services.current_game import CurrentGameProviderImpl
from shvatka.core.services.game_play import CheckKeyInteractor
from shvatka.infrastructure.db.dao.complex.game import GameFilesGetterImpl, GamePlayReaderImpl
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

    @provide
    def game_play_reader(self, dao: HolderDao) -> GamePlayReader:
        return GamePlayReaderImpl(dao)

    game_play_reader_interactor = provide(GamePlayReaderInteractor)

    @provide
    def game_player_dao(self, dao: HolderDao) -> GamePlayerDao:
        return GamePlayerDaoImpl(dao)

    check_key_interactor = provide(CheckKeyInteractor)

    @provide
    def game_by_id_getter(self, dao: HolderDao) -> GameByIdGetter:
        return dao.game

    all_game_keys_reader_interactor = provide(AllGameKeysReaderInteractor)
    transitions_reader_interactor = provide(GameScenarioTransitionsInteractor)
