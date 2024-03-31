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
from shvatka.infrastructure.db.dao.complex.game import GameFilesGetterImpl, GamePlayReaderImpl
from shvatka.infrastructure.db.dao.complex.key_log import GameKeysReaderImpl
from shvatka.infrastructure.db.dao.complex.level_times import GameStatReaderImpl
from shvatka.infrastructure.db.dao.holder import HolderDao


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
