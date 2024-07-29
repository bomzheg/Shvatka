from datetime import datetime
from typing import BinaryIO

from shvatka.core.games.dto import CurrentHints
from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.core.games.adapters import (
    GameFileReader,
    GamePlayReader,
    GameKeysReader,
    GameStatReader,
    GamePlayKeyRepo,
)
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.models import dto
from shvatka.core.rules.game import check_can_read
from shvatka.core.services.game_stat import get_typed_keys, get_game_stat
from shvatka.core.services.game_play import check_key
from shvatka.core.services.key import KeyProcessor
from shvatka.core.services.scenario.files import check_file_meta_can_read
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.core.views.game import GameView, OrgNotifier, GameLogWriter


class GameKeysReaderInteractor:
    def __init__(self, dao: GameKeysReader):
        self.dao = dao

    async def __call__(self, game_id: int, user: dto.User) -> dict[int, list[dto.KeyTime]]:
        player = await self.dao.get_by_user(user)
        game = await self.dao.get_by_id(game_id)
        keys = await get_typed_keys(game, player, self.dao)
        return {t.id: k for t, k in keys.items()}


class GameStatReaderInteractor:
    def __init__(self, dao: GameStatReader):
        self.dao = dao

    async def __call__(self, game_id: int, user: dto.User) -> dto.GameStat:
        player = await self.dao.get_by_user(user)
        game = await self.dao.get_by_id(game_id)
        return await get_game_stat(game, player, self.dao)


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
        if not await self.dao.check_waiver(player, team, game):
            raise exceptions.WaiverError(
                team=team, game=game, player=player, text="игрок не заявлен на игру, но ввёл ключ"
            )
        level_time = await self.dao.get_current_level_time(team, game)
        level = await self.dao.get_level_by_game_and_number(game, level_time.level_number)
        hints = level.get_hints_for_timedelta(datetime.now(tz=tz_utc) - level_time.start_at)
        keys = await self.dao.get_team_typed_keys(game, team, level_time.level_number)
        return CurrentHints(
            hints=hints,
            typed_keys=keys,
            level_number=level_time.level_number,
            started_at=level_time.start_at,
        )


class GamePlayKeyInteractor:
    def __init__(
        self,
        dao: GamePlayKeyRepo,
        view: GameView,
        game_log: GameLogWriter,
        org_notifier: OrgNotifier,
        locker: KeyCheckerFactory,
        key_processor: KeyProcessor,
        scheduler: Scheduler,
    ):
        self.dao = dao
        self.view = view
        self.game_log = game_log
        self.org_notifier = org_notifier
        self.locker = locker
        self.key_processor = key_processor
        self.scheduler = scheduler

    async def __call__(self, user: dto.User, key: str) -> dto.InsertedKey:
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
        if not await self.dao.check_waiver(player, team, game):
            raise exceptions.WaiverError(
                team=team, game=game, player=player, text="игрок не заявлен на игру, но ввёл ключ"
            )
        return await check_key(
            key=key,
            player=player,
            team=team,
            game=game,
            dao=self.dao,
            view=self.view,
            game_log=self.game_log,
            org_notifier=self.org_notifier,
            locker=self.locker,
            key_processor=self.key_processor,
            scheduler=self.scheduler,
        )
