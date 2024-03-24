from dishka import Provider, Scope, provide

from shvatka.core.games.interactors import GameFileReaderInteractor
from shvatka.core.games.adapters import GameFileReader
from shvatka.infrastructure.db.dao.complex.game import GameFilesGetterImpl
from shvatka.infrastructure.db.dao.holder import HolderDao


class DAOProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_game_files(self, dao: HolderDao) -> GameFileReader:
        return GameFilesGetterImpl(dao)


class InteractorProvider(Provider):
    scope = Scope.REQUEST
    file_reader = provide(GameFileReaderInteractor)
