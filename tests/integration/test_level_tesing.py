from datetime import datetime

import pytest

from shvatka.core.models import dto
from shvatka.core.services.level_testing import (
    start_level_test,
    check_level_testing_key,
    send_testing_level_hint,
)
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.core.views.game import LevelTestCompleted
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.mocks.level_view import LevelViewMock
from tests.mocks.org_notifier import OrgNotifierMock
from tests.mocks.scheduler_mock import LevelSchedulerMock


@pytest.mark.asyncio
async def test_level_testing(
    game: dto.FullGame, harry: dto.Player, dao: HolderDao, locker: KeyCheckerFactory
):
    start_at = datetime.now(tz=tz_utc)
    level = game.levels[0]
    scheduler = LevelSchedulerMock()
    level_view = LevelViewMock()
    org_notifier = OrgNotifierMock()
    harry_org = await dao.organizer.add_new(game, harry)
    await dao.commit()
    suite = dto.LevelTestSuite(level=level, tester=harry_org)
    assert not await dao.level_test.is_still_testing(suite)

    await start_level_test(
        suite=suite, scheduler=scheduler, view=level_view, dao=dao.level_testing_complex
    )
    actual_suite, actual_hint_number, actual_run_at = scheduler.calls.pop()
    assert suite == actual_suite
    assert 1 == actual_hint_number
    assert start_at < actual_run_at

    actual_suite = level_view.calls["send_puzzle"].pop()
    assert suite == actual_suite

    assert await dao.level_test.is_still_testing(suite)

    await check_level_testing_key(
        "SH123", suite, level_view, org_notifier, locker, dao.level_testing_complex
    )
    keys = await dao.level_test.get_correct_tested_keys(suite)
    assert {"SH123"} == keys
    keys = await dao.level_test.get_all_typed(suite)
    assert 1 == len(keys)
    assert "SH123" == keys[0].text
    assert keys[0].is_correct
    assert keys[0].at > start_at
    actual_suite, actual_key = level_view.calls["correct_key"].pop()
    assert suite == actual_suite
    assert "SH123" == actual_key

    await check_level_testing_key(
        "SHWRONG", suite, level_view, org_notifier, locker, dao.level_testing_complex
    )
    keys = await dao.level_test.get_correct_tested_keys(suite)
    assert {"SH123"} == keys
    keys = await dao.level_test.get_all_typed(suite)
    assert 2 == len(keys)
    assert "SHWRONG" == keys[1].text
    assert not keys[1].is_correct
    actual_suite, actual_key = level_view.calls["wrong_key"].pop()
    assert suite == actual_suite
    assert "SHWRONG" == actual_key

    await check_level_testing_key(
        "SH321", suite, level_view, org_notifier, locker, dao.level_testing_complex
    )
    assert not await dao.level_test.is_still_testing(suite)
    keys = await dao.level_test.get_correct_tested_keys(suite)
    assert {"SH123", "SH321"} == keys
    keys = await dao.level_test.get_all_typed(suite)
    assert 3 == len(keys)
    assert "SH321" == keys[2].text
    assert keys[2].is_correct
    assert keys[2].at > start_at
    actual_suite, actual_key = level_view.calls["correct_key"].pop()
    assert suite == actual_suite
    assert "SH321" == actual_key
    result = await dao.level_test.get_testing_result(suite)
    assert result.td <= datetime.now(tz=tz_utc) - start_at
    actual_suite = level_view.calls["level_finished"].pop()
    assert suite == actual_suite
    event = org_notifier.calls.pop()
    assert isinstance(event, LevelTestCompleted)
    assert suite == event.suite
    assert result == event.result
    assert 1 == len(event.orgs_list)
    assert game.author.id == event.orgs_list[0].player.id


@pytest.mark.asyncio
async def test_send_hint_for_tester_level(
    game: dto.FullGame, harry: dto.Player, dao: HolderDao, locker: KeyCheckerFactory
):
    start_at = datetime.now(tz=tz_utc)
    level = game.levels[1]
    scheduler = LevelSchedulerMock()
    level_view = LevelViewMock()
    harry_org = await dao.organizer.add_new(game, harry)
    await dao.commit()
    suite = dto.LevelTestSuite(level=level, tester=harry_org)
    await start_level_test(
        suite=suite, scheduler=scheduler, view=level_view, dao=dao.level_testing_complex
    )

    await send_testing_level_hint(suite, 1, level_view, scheduler, dao.level_testing_complex)
    actual_suit, hint_number = level_view.calls["send_hint"].pop()
    assert suite == actual_suit
    assert 1 == hint_number
    actual_suit, hint_number, run_at = scheduler.calls.pop()
    assert suite == actual_suit
    assert 2 == hint_number
    assert run_at > start_at
