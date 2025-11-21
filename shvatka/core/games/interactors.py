from datetime import datetime
from typing import BinaryIO

from shvatka.core.games.dto import CurrentHints
from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.core.games.adapters import (
    GameFileReader,
    GamePlayReader,
    GameKeysReader,
    GameStatReader,
)
from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.rules.game import check_can_read
from shvatka.core.services.game_stat import get_typed_keys, get_game_stat_with_hints
from shvatka.core.services.scenario.files import check_file_meta_can_read
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_utc


class GameKeysReaderInteractor:
    def __init__(self, dao: GameKeysReader):
        self.dao = dao

    async def __call__(
        self, game_id: int, identity: IdentityProvider
    ) -> dict[int, list[dto.KeyTime]]:
        game = await self.dao.get_by_id(game_id)
        keys = await get_typed_keys(game, identity, self.dao)
        return {t.id: k for t, k in keys.items()}


class GameStatReaderInteractor:
    def __init__(self, dao: GameStatReader):
        self.dao = dao

    async def __call__(self, game_id: int, identity: IdentityProvider) -> dto.GameStatWithHints:
        player = await identity.get_required_player()
        game = await self.dao.get_by_id(game_id)
        return await get_game_stat_with_hints(game, player, self.dao)


class GameFileReaderInteractor:
    def __init__(self, dao: GameFileReader, file_gateway: FileGateway):
        self.file_gateway = file_gateway
        self.dao = dao

    async def __call__(self, guid: str, game_id: int, identity: IdentityProvider) -> BinaryIO:
        user = await identity.get_required_user()
        player = await identity.get_required_player()
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
    def __init__(self, dao: GamePlayReader, current_game: CurrentGameProvider):
        self.dao = dao
        self.current_game = current_game

    async def __call__(self, identity: IdentityProvider) -> CurrentHints:
        user = await identity.get_user()
        player = await identity.get_required_player()
        team = await self.dao.get_team(player)
        if not team:
            raise exceptions.PlayerNotInTeam(
                player=player,
                user=user,
            )
        game = await self.current_game.get_required_game()
        if not await self.dao.check_waiver(player, team, game):
            raise exceptions.WaiverError(
                team=team, game=game, player=player, text="игрок не заявлен на игру, но ввёл ключ"
            )
        level_time = await self.dao.get_current_level_time(team, game)
        level = await self.dao.get_level_by_game_and_number(game, level_time.level_number)
        hints_ = level.get_hints_for_timedelta(datetime.now(tz=tz_utc) - level_time.start_at)
        keys = await self.dao.get_team_typed_keys(game, team, level_time)
        return CurrentHints(
            hints=hints_,
            typed_keys=keys,
            level_number=level_time.level_number,
            started_at=level_time.start_at,
        )
