import logging
from zipfile import Path as ZipPath

from dataclass_factory import Factory
from typing.io import BinaryIO

from infrastructure.db.dao.holder import HolderDao
from shvatka.interfaces.clients.file_storage import FileGateway
from shvatka.models import dto
from shvatka.services.game import upsert_game
from shvatka.services.scenario.scn_zip import unpack_scn
from shvatka.utils import exceptions

logger = logging.getLogger(__name__)


def load_scn(
    player: dto.Player,
    dao: HolderDao,
    file_gateway: FileGateway,
    dcf: Factory,
    zip_scn: BinaryIO,
):
    try:
        with unpack_scn(ZipPath(zip_scn)).open() as scn:
            game = await upsert_game(scn, player, dao.game_upserter, dcf, file_gateway)
    except exceptions.ScenarioNotCorrect as e:
        logger.error("game scenario from player %s has problems", player.id, exc_info=e)
        return
    logger.info("successfully loaded game %s", game.id)
