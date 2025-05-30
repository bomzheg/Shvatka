import asyncio
import logging
import typing
from dataclasses import dataclass
from datetime import timedelta, datetime

from shvatka.core.interfaces.dal.game_play import GamePreparer, GamePlayerDao
from shvatka.core.interfaces.dal.level_times import GameStarter, LevelByTeamGetter
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.models import dto, enums
from shvatka.core.models.dto import hints
from shvatka.core.services.key import KeyProcessor
from shvatka.core.services.organizers import get_orgs, get_spying_orgs
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.core.views.game import (
    GameViewPreparer,
    GameLogWriter,
    GameView,
    OrgNotifier,
    LevelUp,
    GameLogEvent,
    GameLogType,
    InputContainer,
)

logger = logging.getLogger(__name__)


async def prepare_game(
    game: dto.Game,
    game_preparer: GamePreparer,
    view_preparer: GameViewPreparer,
):
    if not need_prepare_now(game):
        logger.warning(
            "waked up too early or too late planned %s, now %s",
            game.start_at,
            datetime.now(tz=tz_utc),
        )
        return
    await view_preparer.prepare_game_view(
        game=game,
        teams=await game_preparer.get_agree_teams(game),
        orgs=await get_orgs(game, game_preparer),
        dao=game_preparer,
    )
    await game_preparer.delete_poll_data()


async def start_game(
    game: dto.FullGame,
    dao: GameStarter,
    game_log: GameLogWriter,
    view: GameView,
    scheduler: Scheduler,
):
    """
    Для начала игры нужно сделать несколько вещей:
    * пометить игру как начатую
    * поставить команды на первый уровень
    * отправить загадку первого уровня
    * запланировать подсказку первого уровня
    * записать в лог игры, что игра началась
    """
    now = datetime.now(tz=tz_utc)
    if not need_start_now(game):
        logger.warning("waked up too early or too late planned %s, now %s", game.start_at, now)
        return
    await dao.set_game_started(game)
    logger.info("game %s started", game.id)
    teams = await dao.get_played_teams(game)

    level_times = {}
    for team in teams:
        level_times[team.id] = await dao.set_to_level(team=team, game=game, level_number=0)
    await dao.commit()

    await asyncio.gather(*[view.send_puzzle(team, game.levels[0]) for team in teams])

    await asyncio.gather(
        *[
            schedule_first_hint(scheduler, team, game.levels[0], level_times[team.id].id, now)
            for team in teams
        ]
    )

    await game_log.log(GameLogEvent(GameLogType.GAME_STARTED, {"game": game.name}))


@dataclass
class CheckKeyInteractor:
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

    async def __call__(
        self,
        key: str,
        input_container: InputContainer,
        player: dto.Player,
        team: dto.Team,
        game: dto.FullGame,
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
        if not await self.dao.check_waiver(player, team, game):
            raise exceptions.WaiverError(
                team=team, game=game, player=player, text="игрок не заявлен на игру, но ввёл ключ"
            )

        key_processor = KeyProcessor(game=game, dao=self.dao, locker=self.locker)
        new_key = await key_processor.check_key(key=key, player=player, team=team)
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


async def send_hint(
    level: dto.Level,
    lt_id: int,
    hint_number: int,
    team: dto.Team,
    game: dto.Game,
    dao: LevelByTeamGetter,
    view: GameView,
    scheduler: Scheduler,
):
    """
    Отправить подсказку (запланированную ранее) и запланировать ещё одну.
    Если команда уже на следующем уровне - отправлять не надо.

    :param level: Подсказка относится к уровню.
    :param lt_id: Идентификатор соответствия уровня и команды.
    :param hint_number: Номер подсказки, которую надо отправить.
    :param team: Какой команде надо отправить подсказку.
    :param game: Текущая игра.
    :param dao: Слой доступа к данным.
    :param view: Слой отображения.
    :param scheduler: Планировщик.
    """
    lt = await dao.get_current_level_time(team, game)
    if lt.id != lt_id:
        logger.debug(
            "team %s is not on level %s (should %s, actually %s), skip sending hint #%s",
            team.id,
            level.number_in_game,
            lt_id,
            lt.id,
            hint_number,
        )
        return
    await view.send_hint(team, hint_number, level)
    next_hint_number = hint_number + 1
    if level.is_last_hint(hint_number):
        logger.debug(
            "sent last hint #%s to team %s on level %s, no new scheduling required",
            hint_number,
            team.id,
            level.db_id,
        )
        return
    next_hint_time = calculate_next_hint_time(
        level.get_hint(hint_number),
        level.get_hint(next_hint_number),
    )
    await scheduler.plain_hint(level, team, next_hint_number, lt_id, next_hint_time)


async def schedule_first_hint(
    scheduler: Scheduler,
    team: dto.Team,
    next_level: dto.Level,
    lt_id: int,
    now: datetime,
):
    await scheduler.plain_hint(
        level=next_level,
        team=team,
        hint_number=1,
        lt_id=lt_id,
        run_at=calculate_first_hint_time(next_level, now),
    )


def calculate_first_hint_time(next_level: dto.Level, now: datetime) -> datetime:
    return calculate_next_hint_time(next_level.get_hint(0), next_level.get_hint(1), now)


def calculate_next_hint_time(
    current: hints.TimeHint, next_: hints.TimeHint, now: datetime | None = None
) -> datetime:
    if now is None:
        now = datetime.now(tz=tz_utc)
    return now + calculate_next_hint_timedelta(current, next_)


def calculate_next_hint_timedelta(
    current_hint: hints.TimeHint,
    next_hint: hints.TimeHint,
) -> timedelta:
    return timedelta(minutes=(next_hint.time - current_hint.time))


def need_start_now(game: dto.Game) -> bool:
    if game.start_at is None:
        return False
    utcnow = datetime.now(tz=tz_utc)
    if game.start_at < utcnow:
        if (utcnow - game.start_at) < timedelta(minutes=30):
            return True
        return False
    else:
        if (game.start_at - utcnow) < timedelta(minutes=1):
            return True
        return False


def need_prepare_now(game: dto.Game) -> bool:
    if game.start_at is None:
        return False
    utcnow = datetime.now(tz=tz_utc)
    if game.start_at < utcnow:
        if (utcnow - game.start_at) < timedelta(minutes=35):
            return True
        return False
    else:
        if (game.start_at - utcnow) < timedelta(minutes=6):
            return True
        return False
