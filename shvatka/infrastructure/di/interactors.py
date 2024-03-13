from dishka import Provider, Scope, provide

from shvatka.core.games.interactors import FileReader
from shvatka.core.interfaces.dal.complex import GameFileLoader
from shvatka.infrastructure.db.dao.complex.game import GameFilesGetterImpl
from shvatka.infrastructure.db.dao.holder import HolderDao


class DAOProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_game_files(self, dao: HolderDao) -> GameFileLoader:
        return GameFilesGetterImpl(dao)


class InteractorProvider(Provider):
    scope = Scope.REQUEST
    file_reader = provide(FileReader)
