from dishka import Provider, Scope, provide

from shvatka.core.games.interactors import GameFileReaderInteractor, GamePlayReaderInteractor
from shvatka.core.games.adapters import GameFileReader, GamePlayReader
from shvatka.infrastructure.db.dao.complex.game import GameFilesGetterImpl, GamePlayReaderImpl
from shvatka.infrastructure.db.dao.holder import HolderDao


class GamePlayProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_game_files(self, dao: HolderDao) -> GameFileReader:
        return GameFilesGetterImpl(dao)

    file_reader = provide(GameFileReaderInteractor)

    @provide
    def game_play_reader(self, dao: HolderDao) -> GamePlayReader:
        return GamePlayReaderImpl(dao)

    game_play_reader_interactor = provide(GamePlayReaderInteractor)
