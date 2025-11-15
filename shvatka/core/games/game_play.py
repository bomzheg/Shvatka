import asyncio
import logging
from datetime import timedelta, datetime

from shvatka.core.interfaces.dal.game_play import GamePreparer
from shvatka.core.interfaces.dal.level_times import GameStarter, LevelByTeamGetter
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.models import dto
from shvatka.core.models.dto import hints
from shvatka.core.services.organizers import get_orgs
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.views.game import (
    GameViewPreparer,
    GameLogWriter,
    GameView,
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
    await scheduler.plain_level_event(
        
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
