from datetime import datetime, timezone
from typing import BinaryIO

from shvatka.core.games.dto import CurrentHints
from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.core.games.adapters import GameFileReader, GamePlayReader
from shvatka.core.models import dto
from shvatka.core.rules.game import check_can_read
from shvatka.core.services.scenario.files import check_file_meta_can_read
from shvatka.core.utils import exceptions


class GameFileReaderInteractor:
    def __init__(self, dao: GameFileReader, file_gateway: FileGateway):
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


class GamePlayReaderInteractor:
    def __init__(self, dao: GamePlayReader):
        self.dao = dao

    async def __call__(self, user: dto.User) -> CurrentHints:
        player = await self.dao.get_by_user(user)
        team = await self.dao.get_team(player)
        if not team:
            raise exceptions.PlayerNotInTeam(
                player=player,
                user=user,
            )
        game = await self.dao.get_active_game()
        if game is None:
            raise exceptions.HaveNotActiveGame(game=game, user=user)
        if await self.dao.check_waiver(player, team, game):
            raise exceptions.WaiverError(
                team=team, game=game, player=player, text="игрок не заявлен на игру, но ввёл ключ"
            )
        level_time = await self.dao.get_level_by_team(team)
        level = await self.dao.get_level_by_game_and_number(game, level_time.level_number)
        hints = level.get_hints_for_timedelta(datetime.now(tz=timezone.utc) - level_time.start_at)
        keys = await self.dao.get_team_typed_keys(game, team)
        return CurrentHints(
            hints=hints,
            typed_keys=keys,
            level_number=level_time.level_number,
            started_at=level_time.start_at,
        )
