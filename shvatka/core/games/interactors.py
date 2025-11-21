import typing
from dataclasses import dataclass
from datetime import datetime
from typing import BinaryIO

from shvatka.core.games.dto import CurrentHints
from shvatka.core.games.game_play import schedule_first_hint
from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.core.games.adapters import (
    GameFileReader,
    GamePlayReader,
    GameKeysReader,
    GameStatReader,
)
from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.interfaces.dal.game_play import GamePlayerDao
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.models import dto, enums
from shvatka.core.rules.game import check_can_read
from shvatka.core.services.game_stat import get_typed_keys, get_game_stat_with_hints
from shvatka.core.services.key import TimerProcessor, KeyProcessor
from shvatka.core.services.organizers import get_spying_orgs
from shvatka.core.services.scenario.files import check_file_meta_can_read
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.core.views.game import (
    GameView,
    GameLogWriter,
    OrgNotifier,
    InputContainer,
    LevelUp,
    GameLogEvent,
    GameLogType,
)
from shvatka.infrastructure.scheduler import SchedulerContainer


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


@dataclass(kw_only=True)
class GamePlayBaseInteractor:
    """
    :param dao: Слой доступа к бд.
    :param view: Слой отображения данных.
    :param game_log: Логгер игры (публичные уведомления о статусе игры).
    :param org_notifier: Для уведомления оргов о важных событиях.
    :param locker: Локи для обеспечения последовательного исполнения определённых операций.
    :param scheduler: Планировщик подсказок.
    """

    dao: GamePlayerDao
    view: GameView
    game_log: GameLogWriter
    org_notifier: OrgNotifier
    locker: KeyCheckerFactory
    scheduler: Scheduler
    current_game: CurrentGameProvider

    async def finish_team(
        self,
        input_container: InputContainer,
        team: dto.Team,
        game: dto.FullGame,
    ):
        """
        Два варианта:
        * уровень последний - поздравляем команду с завершением игры
        * уровень последний и все команды финишировали - помечаем игру законченной,
          пишем в лог игры уведомление о финале, уведомляем команды.
        """
        await self.view.game_finished(team, input_container)
        if await self.dao.is_all_team_finished(game):
            await self.dao.finish(game)
            await self.dao.commit()
            await self.game_log.log(GameLogEvent(GameLogType.GAME_FINISHED, {"game": game.name}))
            self.locker.clear()
            for team in await self.dao.get_played_teams(game):
                await self.view.game_finished_by_all(team)

    async def process_level_up(
        self,
        input_container: InputContainer,
        team: dto.Team,
        game: dto.FullGame,
    ):
        async with self.locker.lock_globally():
            if await self.dao.is_team_finished(team, game):
                await self.finish_team(input_container, team, game)
                return
        next_level = await self.dao.get_current_level(team, game)
        lt = await self.dao.get_current_level_time(team, game)

        await self.view.send_puzzle(team=team, level=next_level)
        await schedule_first_hint(
            scheduler=self.scheduler,
            team=team,
            next_level=next_level,
            lt_id=lt.id,
            now=datetime.now(tz=tz_utc),
        )
        level_up_event = LevelUp(
            team=team, new_level=next_level, orgs_list=await get_spying_orgs(game, self.dao)
        )
        await self.org_notifier.notify(level_up_event)


@dataclass(kw_only=True)
class CheckKeyInteractor(GamePlayBaseInteractor):
    key_processor: KeyProcessor

    async def __call__(
        self,
        key: str,
        input_container: InputContainer,
        identity: IdentityProvider,
    ):
        """
        Проверяет введённый игроком ключ. Может случиться несколько исходов:
        - ключ неверный - просто записываем его в лог и уведомляем команду
        - ключ верный, но уже был введён ранее - записываем в лог и уведомляем команду
        - ключ верный, но ещё не все ключи найдены - записываем в лог, уведомляем команду
        - ключ верный и больше на уровне не осталось ненайденных ключей:
          * уровень не последний - переводим команду на следующий уровень, уведомляем оргов,
            присылаем команде новую загадку, планируем отправку подсказки
          * уровень последний - поздравляем команду с завершением игры
          * уровень последний и все команды финишировали - помечаем игру законченной,
            пишем в лог игры уведомление о финале, уведомляем команды

        :param key: Введённый ключ.
        :param player: Игрок, который ввёл ключ.
        :param team: Команда, в которой ввели ключ.
        :param game: Текущая игра.
        """
        game = await self.current_game.get_required_full_game()
        player = await identity.get_required_player()
        team = await identity.get_required_team()
        if not await self.dao.check_waiver(player, team, game):
            raise exceptions.WaiverError(
                team=team, game=game, player=player, text="игрок не заявлен на игру, но ввёл ключ"
            )

        new_key = await self.key_processor.check_key(key=key, player=player, team=team)
        if new_key is None:
            return
        if new_key.is_duplicate:
            await self.view.duplicate_key(key=new_key, input_container=input_container)
            return
        match new_key.type_:
            case enums.KeyType.wrong:
                await self.view.wrong_key(key=new_key, input_container=input_container)
            case enums.KeyType.bonus:
                assert isinstance(new_key.parsed_key, dto.ParsedBonusKey)
                await self.view.bonus_key(
                    new_key, new_key.parsed_key.bonus_minutes, input_container=input_container
                )
            case enums.KeyType.bonus_hint:
                assert isinstance(new_key.parsed_key, dto.ParsedBonusHintKey)
                await self.view.bonus_hint_key(
                    new_key, new_key.parsed_key.bonus_hint, input_container=input_container
                )
            case enums.KeyType.simple:
                await self.view.correct_key(key=new_key, input_container=input_container)
                if new_key.is_level_up:
                    await self.process_level_up(
                        input_container=input_container,
                        team=team,
                        game=game,
                    )
            case _:
                typing.assert_never(new_key.type_)


@dataclass(kw_only=True)
class GamePlayTimerInteractor(GamePlayBaseInteractor):
    processor: TimerProcessor

    async def __call__(
        self,
        team_id: int,
        now: datetime,
        started_level_time_id: int,
        input_container: SchedulerContainer,
    ) -> None:
        team = await self.dao.get_by_id(team_id)
        effects_list = await self.processor.process(
            team=team,
            now=now,
            started_level_time_id=started_level_time_id,
        )

        if not effects_list:
            return
        game = await self.current_game.get_required_full_game()
        level_time = await self.dao.get_current_level_time(team, game)
        for effects in effects_list:
            await self.dao.save_event(team=team, level_time=level_time, game=game, effects=effects)
            if effects.hints_:
                await self.view.hint(hint=effects.hints_, input_container=input_container)
            if effects.bonus_minutes:
                await self.view.bonus(bonus=effects.bonus_minutes, input_container=input_container)
            if effects.level_up:
                team = await self.dao.get_by_id(team_id)
                await self.process_level_up(
                    input_container=input_container,
                    team=team,
                    game=await self.current_game.get_required_full_game(),
                )
        await self.dao.commit()
