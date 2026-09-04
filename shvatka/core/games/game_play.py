import asyncio
import logging
from datetime import datetime, timedelta

from shvatka.core.interfaces.dal.game_play import GamePreparer
from shvatka.core.interfaces.dal.level_times import GameStarter, LevelByTeamGetter
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.models import dto
from shvatka.core.models.dto import action, hints
from shvatka.core.services.organizers import get_orgs
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.views.game import (
    GameLogEvent,
    GameLogType,
    GameViewPreparer,
    SendHint,
    SendPuzzle,
    ShowTasks,
    ViewSender,
)

logger = logging.getLogger(__name__)

START_SNAP = timedelta(seconds=2)
"""На столько планировщик имеет право промахнуться мимо назначенного старта игры."""


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
    sender: ViewSender,
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

    started_at = snap_to_planned_start(game.start_at, now)
    level_times = {}
    for team in teams:
        level_times[team.id] = await dao.set_to_level(
            team=team, game=game, level_number=0, at=started_at
        )
    await dao.commit()

    tasks = ShowTasks(view=[SendPuzzle(team=team, level=game.levels[0]) for team in teams])

    await asyncio.gather(
        *[
            schedule_first_hint(
                scheduler=scheduler,
                team=team,
                next_level=game.levels[0],
                lt_id=level_times[team.id].id,
                level_started_at=level_times[team.id].start_at,
            )
            for team in teams
        ]
    )

    tasks.log.append(GameLogEvent(GameLogType.GAME_STARTED, {"game": game.name}))
    await sender.show_later(tasks)


async def send_hint(
    level: dto.Level,
    lt_id: int,
    hint_number: int,
    team: dto.Team,
    game: dto.Game,
    dao: LevelByTeamGetter,
    sender: ViewSender,
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
    :param sender: Отправляет то, что надо показать, во вьюхи.
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
    await sender.show_later(
        ShowTasks(view=[SendHint(team=team, hint_number=hint_number, level=level)])
    )
    next_hint_number = hint_number + 1
    if level.is_last_hint(hint_number):
        logger.debug(
            "sent last hint #%s to team %s on level %s, no new scheduling required",
            hint_number,
            team.id,
            level.db_id,
        )
        return
    # время подсказки считаем от начала уровня, не от момента отправки предыдущей:
    # иначе задержки планировщика копятся от подсказки к подсказке
    next_hint_time = calculate_hint_time(lt.start_at, level.get_hint(next_hint_number))
    await scheduler.plain_hint(level, team, next_hint_number, lt_id, next_hint_time)


async def schedule_first_hint(
    scheduler: Scheduler,
    team: dto.Team,
    next_level: dto.Level,
    lt_id: int,
    level_started_at: datetime,
):
    if (next_hint_at := calculate_first_hint_time(next_level, level_started_at)) is not None:
        await scheduler.plain_hint(
            level=next_level,
            team=team,
            hint_number=1,
            lt_id=lt_id,
            run_at=next_hint_at,
        )
    for condition in next_level.scenario.conditions:
        if isinstance(condition, action.LevelTimerEffectsCondition):
            await scheduler.plain_level_event(
                team=team,
                lt_id=lt_id,
                run_at=level_started_at + condition.get_action_time(),
                effects=condition.effects,
            )


def calculate_first_hint_time(
    next_level: dto.Level, level_started_at: datetime
) -> datetime | None:
    if next_level.is_last_hint(0):
        return None
    return calculate_hint_time(level_started_at, next_level.get_hint(1))


def calculate_hint_time(level_started_at: datetime, hint: hints.TimeHint) -> datetime:
    """
    Момент отправки подсказки — фиксированное смещение от начала уровня.

    Единственный правильный способ её посчитать: если считать от предыдущей подсказки,
    задержки доставки будут копиться от подсказки к подсказке.
    """
    return level_started_at + timedelta(minutes=hint.time)


def snap_to_planned_start(planned: datetime | None, now: datetime) -> datetime:
    if planned is None:
        return now
    if abs(now - planned) <= START_SNAP:
        return planned
    logger.info(
        "game started at %s, %s away from planned %s, so planned start is not used",
        now,
        abs(now - planned),
        planned,
    )
    return now


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
