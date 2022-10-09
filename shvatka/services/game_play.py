import asyncio
import logging
from datetime import timedelta, datetime

from shvatka.dal.game_play import GamePreparer, KeyChecker
from shvatka.dal.level_times import GameStarter, LevelTimeChecker
from shvatka.models import dto
from shvatka.models.dto.scn.time_hint import TimeHint
from shvatka.scheduler import Scheduler
from shvatka.utils.key_checker_lock import KeyCheckerFactory
from shvatka.views.game import GameViewPreparer, GameLogWriter, GameView, OrgNotifier, LevelUp

logger = logging.getLogger(__name__)


async def prepare_game(game: dto.Game, game_preparer: GamePreparer, view_preparer: GameViewPreparer):
    await game_preparer.delete_poll_data()
    await view_preparer.prepare_game_view(
        game=game,
        teams=await game_preparer.get_agree_teams(game),
        orgs=await game_preparer.get_orgs(game),
    )


async def start_game(
    game: dto.FullGame,
    dao: GameStarter,
    game_log: GameLogWriter,
    view: GameView,
    scheduler: Scheduler,
):
    now = datetime.utcnow()
    await dao.set_game_started(game)
    logger.info("game %s started", game.id)

    teams = await dao.get_played_teams(game)

    await dao.set_teams_to_first_level(game, teams)

    puzzle = game.get_hint(0, 0)
    await asyncio.gather(*[view.send_puzzle(team, puzzle) for team in teams])

    hint = game.get_hint(0, 1)

    hint_time = now + calculate_next_hint_timedelta(puzzle, hint)
    await asyncio.gather(*[scheduler.plain_hint(game.levels[0], team, 1, hint_time) for team in teams])

    await dao.commit()
    await game_log.log("Game started")


async def check_key(
    key: str,
    player: dto.Player,
    team: dto.Team,
    game: dto.Game,
    dao: KeyChecker,
    view: GameView,
    game_log: GameLogWriter,
    org_notifier: OrgNotifier,
    locker: KeyCheckerFactory,
):
    async with locker(team):
        level = await dao.get_current_level(team, game)
        keys = level.get_keys()
        is_correct = key in keys
        typed_keys = await dao.get_correct_typed_keys(level=level, game=game, team=team)
        if is_correct:
            if key in typed_keys:
                is_correct = None
            else:
                typed_keys.add(key)
        await dao.save_key(key=key, team=team, level=level, game=game, player=player, is_correct=is_correct)
        is_level_up = False
        if typed_keys == keys:
            await dao.level_up(team=team, level=level, game=game)
            is_level_up = True
        await dao.commit()

    if is_correct is None:
        await view.duplicate_key(team=team, key=key)
    elif is_level_up:
        # TODO check finish game
        next_level = await dao.get_current_level(team, game)
        await view.send_puzzle(team=team, puzzle=next_level.get_hint(0))
        await org_notifier.notify(LevelUp(team=team, new_level=next_level))
    else:
        await view.correct_key(team=team)


async def send_hint(
    level: dto.Level,
    hint_number: int,
    team: dto.Team,
    dao: LevelTimeChecker,
    view: GameView,
    scheduler: Scheduler,
):
    if not await dao.is_team_on_level(team, level):
        logger.debug("team %s is not on level %s, skip sending hint #%s", team.id, level.db_id, hint_number)
        return
    await view.send_hint(team, level.get_hint(hint_number))
    next_hint_number = hint_number + 1
    if level.is_last_hint(next_hint_number):
        logger.debug(
            "sent last hint #%s to team %s on level %s, no new scheduling required",
            hint_number, team.id, level.db_id,
        )
        return
    next_hint_time = datetime.utcnow() + calculate_next_hint_timedelta(
        level.get_hint(hint_number), level.get_hint(next_hint_number),
    )
    await scheduler.plain_hint(level, team, next_hint_number, next_hint_time)


def calculate_next_hint_timedelta(current_hint: TimeHint, next_hint: TimeHint) -> timedelta:
    return timedelta(minutes=(next_hint.time - current_hint.time))
