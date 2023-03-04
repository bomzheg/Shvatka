import logging
from datetime import datetime

from shvatka.core.interfaces.dal.game import GameByIdGetter
from shvatka.core.interfaces.dal.level_testing import LevelTestingDao
from shvatka.core.interfaces.scheduler import LevelTestScheduler
from shvatka.core.models import dto
from shvatka.core.services.game_play import calculate_first_hint_time, calculate_next_hint_time
from shvatka.core.services.organizers import get_primary_orgs
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.utils.exceptions import InvalidKey
from shvatka.core.utils.input_validation import is_key_valid
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.core.views.game import OrgNotifier, LevelTestCompleted
from shvatka.core.views.level import LevelView

logger = logging.getLogger(__name__)


async def start_level_test(
    suite: dto.LevelTestSuite,
    scheduler: LevelTestScheduler,
    view: LevelView,
    dao: LevelTestingDao,
):
    now = datetime.now(tz=tz_utc)
    await view.send_puzzle(suite=suite)
    await scheduler.plain_test_hint(
        suite=suite,
        hint_number=1,
        run_at=calculate_first_hint_time(suite.level, now),
    )
    await dao.save_started_level_test(suite=suite, now=now)
    await dao.commit()


async def send_testing_level_hint(
    suite: dto.LevelTestSuite,
    hint_number: int,
    view: LevelView,
    scheduler: LevelTestScheduler,
    dao: LevelTestingDao,
):
    if not await dao.is_still_testing(suite=suite):
        logger.debug(
            "testing %s (%s) completed by player %s, hint doesn't need",
            suite.level.db_id,
            suite.level.name_id,
            suite.tester.player.id,
        )
        return
    await view.send_hint(hint_number=hint_number, suite=suite)
    next_hint_number = hint_number + 1
    if suite.level.is_last_hint(hint_number):
        logger.debug(
            "send last hint #%s to player %s by testing level %s (%s)",
            hint_number,
            suite.tester.player.id,
            suite.level.db_id,
            suite.level.name_id,
        )
        return
    next_hint_time = calculate_next_hint_time(
        suite.level.get_hint(hint_number),
        suite.level.get_hint(next_hint_number),
    )
    await scheduler.plain_test_hint(
        suite=suite,
        hint_number=next_hint_number,
        run_at=next_hint_time,
    )


async def check_level_testing_key(
    key: str,
    suite: dto.LevelTestSuite,
    view: LevelView,
    org_notifier: OrgNotifier,
    locker: KeyCheckerFactory,
    dao: LevelTestingDao,
):
    if not is_key_valid(key):
        raise InvalidKey(key=key, player=suite.tester.player)
    async with locker.lock_player(suite.tester.player):
        keys = suite.level.get_keys()
        is_correct_key = key in keys
        await dao.save_key(
            key=key,
            suite=suite,
            is_correct=is_correct_key,
        )
        typed_keys = await dao.get_correct_tested_keys(suite=suite)
        is_completed = False
        if typed_keys == keys:
            await dao.complete_test(suite=suite)
            is_completed = True
        await dao.commit()
    if not is_correct_key:
        await view.wrong_key(suite=suite, key=key)
        return
    await view.correct_key(suite=suite, key=key)
    if is_completed:
        await view.level_finished(suite=suite)
        event = LevelTestCompleted(
            suite=suite,
            orgs_list=await get_testing_observers(level=suite.level, dao=dao),
            result=await dao.get_testing_result(suite=suite),
        )
        await org_notifier.notify(event)


async def get_testing_observers(level: dto.Level, dao: GameByIdGetter) -> list[dto.Organizer]:
    game = await dao.get_by_id(level.game_id)
    return await get_primary_orgs(game=game)
