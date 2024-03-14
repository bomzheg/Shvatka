from typing import BinaryIO

from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.core.interfaces.dal.complex import GameFileLoader
from shvatka.core.models import dto
from shvatka.core.rules.game import check_can_read
from shvatka.core.services.scenario.files import check_file_meta_can_read
from shvatka.core.utils import exceptions


class FileReader:
    def __init__(self, dao: GameFileLoader, file_gateway: FileGateway):
        self.file_gateway = file_gateway
        self.dao = dao

    async def __call__(self, guid: str, game_id: int, user: dto.User) -> BinaryIO:
        player = await self.dao.get_by_user(user)
        game = await self.dao.get_full(game_id)
        check_can_read(game, player)
        if guid not in game.get_guids():
            raise exceptions.FileNotFound(
                text=f"There is no file with uuid {guid} associated with game id {game_id}",
                game_id=game_id,
                game=game,
                user_id=user.db_id,
                user=user,
                player_id=player.id,
                player=player,
            )
        meta = await self.dao.get_by_guid(guid)
        check_file_meta_can_read(player, meta, game)
        return await self.file_gateway.get(meta)
