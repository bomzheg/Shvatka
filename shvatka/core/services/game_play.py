import asyncio
import logging
import typing
from datetime import timedelta, datetime

from shvatka.core.interfaces.dal.game_play import GamePreparer, GamePlayerDao
from shvatka.core.interfaces.dal.level_times import GameStarter, LevelTimeChecker
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.models import dto, enums
from shvatka.core.models.dto import scn
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

    await dao.set_teams_to_first_level(game, teams)
    await dao.commit()

    await asyncio.gather(*[view.send_puzzle(team, game.levels[0]) for team in teams])

    await asyncio.gather(
        *[schedule_first_hint(scheduler, team, game.levels[0], now) for team in teams]
    )

    await game_log.log(GameLogEvent(GameLogType.GAME_STARTED, {"game": game.name}))


async def check_key(
    key: str,
    player: dto.Player,
    team: dto.Team,
    game: dto.FullGame,
    dao: GamePlayerDao,
    view: GameView,
    game_log: GameLogWriter,
    org_notifier: OrgNotifier,
    locker: KeyCheckerFactory,
    key_processor: KeyProcessor,
    scheduler: Scheduler,
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
    :param dao: Слой доступа к бд.
    :param view: Слой отображения данных.
    :param game_log: Логгер игры (публичные уведомления о статусе игры).
    :param org_notifier: Для уведомления оргов о важных событиях.
    :param locker: Локи для обеспечения последовательного исполнения определённых операций.
    :param key_processor: Логика работы с ключами
    :param scheduler: Планировщик подсказок.
    """
    if not await dao.check_waiver(player, team, game):
        raise exceptions.WaiverError(
            team=team, game=game, player=player, text="игрок не заявлен на игру, но ввёл ключ"
        )

    new_key = await key_processor.check_key(key=key, player=player, team=team)
    if new_key.is_duplicate:
        await view.duplicate_key(key=new_key)
        return
    match new_key.type_:
        case enums.KeyType.wrong:
            await view.wrong_key(key=new_key)
        case enums.KeyType.bonus:
            assert isinstance(new_key.parsed_key, dto.ParsedBonusKey)
            await view.bonus_key(new_key, new_key.parsed_key.bonus_minutes)
        case enums.KeyType.simple:
            await view.correct_key(key=new_key)
            if new_key.is_level_up:
                await process_level_up(
                    team=team,
                    game=game,
                    dao=dao,
                    view=view,
                    game_log=game_log,
                    org_notifier=org_notifier,
                    locker=locker,
                    scheduler=scheduler,
                )
        case _:
            typing.assert_never(new_key.type_)


async def process_level_up(
    team: dto.Team,
    game: dto.FullGame,
    dao: GamePlayerDao,
    view: GameView,
    game_log: GameLogWriter,
    org_notifier: OrgNotifier,
    locker: KeyCheckerFactory,
    scheduler: Scheduler,
):
    async with locker.lock_globally():
        if await dao.is_team_finished(team, game):
            await finish_team(team, game, view, game_log, dao, locker)
            return
    next_level = await dao.get_current_level(team, game)

    await view.send_puzzle(team=team, level=next_level)
    await schedule_first_hint(scheduler, team, next_level)
    level_up_event = LevelUp(
        team=team, new_level=next_level, orgs_list=await get_spying_orgs(game, dao)
    )
    await org_notifier.notify(level_up_event)


async def finish_team(
    team: dto.Team,
    game: dto.FullGame,
    view: GameView,
    game_log: GameLogWriter,
    dao: GamePlayerDao,
    locker: KeyCheckerFactory,
):
    """
    Два варианта:
    * уровень последний - поздравляем команду с завершением игры
    * уровень последний и все команды финишировали - помечаем игру законченной,
      пишем в лог игры уведомление о финале, уведомляем команды.
    :param team: Команда закончившая игру.
    :param game: Текущая игра.
    :param dao: Слой доступа к бд.
    :param view: Слой отображения данных.
    :param game_log: Логгер игры (публичные уведомления о статусе игры).
    :param locker: Эту штуку мы просто очистим, если игра кончилась.
    """
    await view.game_finished(team)
    if await dao.is_all_team_finished(game):
        await dao.finish(game)
        await dao.commit()
        await game_log.log(GameLogEvent(GameLogType.GAME_FINISHED, {"game": game.name}))
        locker.clear()
        for team in await dao.get_played_teams(game):
            await view.game_finished_by_all(team)


async def send_hint(
    level: dto.Level,
    hint_number: int,
    team: dto.Team,
    dao: LevelTimeChecker,
    view: GameView,
    scheduler: Scheduler,
):
    """
    Отправить подсказку (запланированную ранее) и запланировать ещё одну.
    Если команда уже на следующем уровне - отправлять не надо.

    :param level: Подсказка относится к уровню.
    :param hint_number: Номер подсказки, которую надо отправить.
    :param team: Какой команде надо отправить подсказку.
    :param dao: Слой доступа к данным.
    :param view: Слой отображения.
    :param scheduler: Планировщик.
    """
    if not await dao.is_team_on_level(team, level):
        logger.debug(
            "team %s is not on level %s, skip sending hint #%s",
            team.id,
            level.db_id,
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
    await scheduler.plain_hint(level, team, next_hint_number, next_hint_time)


async def schedule_first_hint(
    scheduler: Scheduler,
    team: dto.Team,
    next_level: dto.Level,
    now: datetime | None = None,
):
    await scheduler.plain_hint(
        level=next_level,
        team=team,
        hint_number=1,
        run_at=calculate_first_hint_time(next_level, now),
    )


def calculate_first_hint_time(next_level: dto.Level, now: datetime | None = None) -> datetime:
    return calculate_next_hint_time(next_level.get_hint(0), next_level.get_hint(1), now)


def calculate_next_hint_time(
    current: scn.TimeHint, next_: scn.TimeHint, now: datetime | None = None
) -> datetime:
    if now is None:
        now = datetime.now(tz=tz_utc)
    return now + calculate_next_hint_timedelta(current, next_)


def calculate_next_hint_timedelta(
    current_hint: scn.TimeHint,
    next_hint: scn.TimeHint,
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
