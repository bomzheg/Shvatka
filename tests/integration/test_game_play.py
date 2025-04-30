from contextlib import suppress
from datetime import datetime, timedelta

import pytest
from dishka import AsyncContainer

from shvatka.core.games.interactors import GamePlayReaderInteractor
from shvatka.core.models import dto, enums
from shvatka.core.models.dto import hints
from shvatka.core.models.enums import GameStatus
from shvatka.core.services.game_play import start_game, send_hint, CheckKeyInteractor
from shvatka.core.services.game_stat import get_typed_keys
from shvatka.core.services.organizers import get_orgs
from shvatka.core.services.player import join_team, leave
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.core.views.game import (
    LevelUp,
    GameLogEvent,
    GameLogType, InputContainer,
)
from shvatka.infrastructure.db import models
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.integration.conftest import dishka_request
from tests.mocks.game_log import GameLogWriterMock
from tests.mocks.game_view import GameViewMock
from tests.mocks.org_notifier import OrgNotifierMock
from tests.mocks.scheduler_mock import SchedulerMock
from tests.utils.time_key import assert_time_key


class MockInputContainer(InputContainer):
    pass

@pytest.mark.asyncio
async def test_start_game(
    game_with_waivers: dto.FullGame,
    gryffindor: dto.Team,
    slytherin: dto.Team,
    author: dto.Player,
    harry: dto.Player,
    ron: dto.Player,
    hermione: dto.Player,
    draco: dto.Player,
    dao: HolderDao,
    check_dao: HolderDao,
    scheduler: SchedulerMock,
):
    dummy_view = GameViewMock()
    dummy_log = GameLogWriterMock()
    game_with_waivers.start_at = datetime.now(tz=tz_utc)

    await start_game(game_with_waivers, dao.game_starter, dummy_log, dummy_view, scheduler)

    dummy_log.assert_one_event(
        GameLogEvent(GameLogType.GAME_STARTED, {"game": game_with_waivers.name})
    )
    scheduler.assert_only_one_hint_for_team(game_with_waivers.levels[0], gryffindor, 1)
    scheduler.assert_only_one_hint_for_team(game_with_waivers.levels[0], slytherin, 1)
    scheduler.assert_no_unchecked()
    dummy_view.assert_send_only_puzzle_for_team(gryffindor, game_with_waivers.levels[0])
    dummy_view.assert_send_only_puzzle_for_team(slytherin, game_with_waivers.levels[0])
    dummy_view.assert_no_unchecked()
    assert 2 == await check_dao.level_time.count()


@pytest.mark.asyncio
async def test_wrong_key(
    author: dto.Player,
    harry: dto.Player,
    gryffindor: dto.Team,
    started_game: dto.FullGame,
    dao: HolderDao,
    check_dao: HolderDao,
    locker: KeyCheckerFactory,
    scheduler: SchedulerMock,
    dishka_request: AsyncContainer,
):
    game = started_game
    dummy_view = GameViewMock()
    dummy_log = GameLogWriterMock()

    dummy_org_notifier = OrgNotifierMock()
    key_checker = CheckKeyInteractor(
        dao=dao.game_player,
        view=dummy_view,
        game_log=dummy_log,
        org_notifier=dummy_org_notifier,
        locker=locker,
        scheduler=scheduler,
    )
    await key_checker(
        key="SHWRONG",
        input_container=MockInputContainer(),
        player=harry,
        team=gryffindor,
        game=game,
    )

    keys = await get_typed_keys(game=game, player=author, dao=check_dao.typed_keys)
    assert [gryffindor] == list(keys.keys())
    assert 1 == len(keys[gryffindor])
    expected_first_key = dto.KeyTime(
        text="SHWRONG",
        type_=enums.KeyType.wrong,
        is_duplicate=False,
        at=datetime.now(tz=tz_utc),
        level_number=0,
        player=harry,
        team=gryffindor,
    )
    assert_time_key(expected_first_key, list(keys[gryffindor])[0])
    dummy_view.assert_wrong_key_only(expected_first_key)


@pytest.mark.asyncio
async def test_bonus_hint_key(
    author: dto.Player,
    harry: dto.Player,
    gryffindor: dto.Team,
    started_game: dto.FullGame,
    dao: HolderDao,
    check_dao: HolderDao,
    locker: KeyCheckerFactory,
    scheduler: SchedulerMock,
):
    game = started_game
    dummy_view = GameViewMock()
    dummy_log = GameLogWriterMock()

    dummy_org_notifier = OrgNotifierMock()
    check_key = CheckKeyInteractor(
        dao=dao.game_player,
        view=dummy_view,
        game_log=dummy_log,
        org_notifier=dummy_org_notifier,
        locker=locker,
        scheduler=scheduler,
    )
    await check_key(
        key="SHBONUSHINT",
        input_container=MockInputContainer(),
        player=harry,
        team=gryffindor,
        game=game,
    )

    keys = await get_typed_keys(game=game, player=author, dao=check_dao.typed_keys)
    assert [gryffindor] == list(keys.keys())
    assert 1 == len(keys[gryffindor])
    expected_first_key = dto.KeyTime(
        text="SHBONUSHINT",
        type_=enums.KeyType.bonus_hint,
        is_duplicate=False,
        at=datetime.now(tz=tz_utc),
        level_number=0,
        player=harry,
        team=gryffindor,
    )
    assert_time_key(expected_first_key, list(keys[gryffindor])[0])
    dummy_view.asser_bonus_hint_key_only(
        expected_first_key,
        [
            hints.GPSHint(type="gps", latitude=55.579282598950165, longitude=37.910306366539395),
            hints.TextHint(type="text", text="this is bonus hint"),
        ],
    )


@pytest.mark.asyncio
async def test_game_play(
    dao: HolderDao,
    locker: KeyCheckerFactory,
    check_dao: HolderDao,
    scheduler: SchedulerMock,
    author: dto.Player,
    harry: dto.Player,
    draco: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    started_game: dto.FullGame,
):
    game = started_game
    # delete slytherin from game
    await leave(draco, draco, dao.team_leaver)

    dummy_view = GameViewMock()
    dummy_log = GameLogWriterMock()

    await send_hint(
        level=game.levels[0],
        hint_number=1,
        lt_id=(await dao.level_time.get_current_level_time(gryffindor, game)).id,
        team=gryffindor,
        game=game,
        dao=dao.level_time,
        view=dummy_view,
        scheduler=scheduler,
    )
    scheduler.assert_one_planned_hint(game.levels[0], gryffindor, 2)
    dummy_view.assert_send_only_hint(gryffindor, 1, game.levels[0])

    dummy_org_notifier = OrgNotifierMock()
    orgs = await get_orgs(game, dao.organizer)
    key_kwargs = {
        "player": harry,
        "team": gryffindor,
        "input_container": MockInputContainer(),
        "game": game,
    }

    check_key = CheckKeyInteractor(
        dao=dao.game_player,
        view=dummy_view,
        game_log=dummy_log,
        org_notifier=dummy_org_notifier,
        locker=locker,
        scheduler=scheduler,
    )
    await check_key(key="SH123", **key_kwargs)
    expected_first_key = dto.KeyTime(
        text="SH123",
        type_=enums.KeyType.simple,
        is_duplicate=False,
        at=datetime.now(tz=tz_utc),
        level_number=0,
        player=harry,
        team=gryffindor,
    )
    dummy_view.assert_correct_key_only(expected_first_key)

    await check_key(key="SH123", **key_kwargs)
    expected_second_key = dto.KeyTime(
        text="SH123",
        type_=enums.KeyType.simple,
        is_duplicate=True,
        at=datetime.now(tz=tz_utc),
        level_number=0,
        player=harry,
        team=gryffindor,
    )
    dummy_view.assert_duplicate_key_only(expected_second_key)

    await check_key(key="SH321", **key_kwargs)
    expected_third_key = dto.KeyTime(
        text="SH321",
        type_=enums.KeyType.simple,
        is_duplicate=False,
        at=datetime.now(tz=tz_utc),
        level_number=0,
        player=harry,
        team=gryffindor,
    )
    dummy_org_notifier.assert_one_event(
        LevelUp(team=gryffindor, new_level=game.levels[1], orgs_list=orgs)
    )
    dummy_view.assert_correct_key_only(expected_third_key)
    dummy_view.assert_send_only_puzzle(gryffindor, game.levels[1])

    await check_key(key="SHOOT", **key_kwargs)
    dummy_log.assert_one_event(GameLogEvent(GameLogType.GAME_FINISHED, {"game": game.name}))
    expected_fourth_key = dto.KeyTime(
        text="SHOOT",
        type_=enums.KeyType.simple,
        is_duplicate=False,
        at=datetime.now(tz=tz_utc),
        level_number=1,
        player=harry,
        team=gryffindor,
    )
    dummy_view.assert_correct_key_only(expected_fourth_key)
    dummy_view.assert_game_finished_only(gryffindor)
    dummy_view.assert_game_finished_all({gryffindor})

    keys = await get_typed_keys(game=game, player=author, dao=check_dao.typed_keys)

    assert [gryffindor] == list(keys.keys())
    assert 4 == len(keys[gryffindor])
    assert_time_key(expected_first_key, list(keys[gryffindor])[0])
    assert_time_key(expected_second_key, list(keys[gryffindor])[1])
    assert_time_key(expected_third_key, list(keys[gryffindor])[2])
    assert_time_key(expected_fourth_key, list(keys[gryffindor])[3])
    assert await dao.game_player.is_all_team_finished(game)
    assert GameStatus.finished == (await dao.game.get_by_id(game.id, author)).status
    dummy_view.assert_no_unchecked()
    dummy_org_notifier.assert_no_calls()


@pytest.mark.asyncio
async def test_fast_play_routed_game(
    dao: HolderDao,
    locker: KeyCheckerFactory,
    check_dao: HolderDao,
    scheduler: SchedulerMock,
    author: dto.Player,
    harry: dto.Player,
    draco: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    started_routed_game: dto.FullGame,
):
    game = started_routed_game
    # delete slytherin from game
    await leave(draco, draco, dao.team_leaver)
    dummy_view = GameViewMock()
    dummy_log = GameLogWriterMock()

    dummy_org_notifier = OrgNotifierMock()
    orgs = await get_orgs(game, dao.organizer)
    key_kwargs = {
        "player": harry,
        "team": gryffindor,
        "input_container": MockInputContainer(),
        "game": game,
    }

    check_key = CheckKeyInteractor(
        dao=dao.game_player,
        view=dummy_view,
        game_log=dummy_log,
        org_notifier=dummy_org_notifier,
        locker=locker,
        scheduler=scheduler,
    )

    await check_key(key="SHTO3", **key_kwargs)
    expected_first_key = dto.KeyTime(
        text="SHTO3",
        type_=enums.KeyType.simple,
        is_duplicate=False,
        at=datetime.now(tz=tz_utc),
        level_number=0,
        player=harry,
        team=gryffindor,
    )
    dummy_view.assert_correct_key_only(expected_first_key)
    dummy_org_notifier.assert_one_event(
        LevelUp(team=gryffindor, new_level=game.levels[2], orgs_list=orgs)
    )
    dummy_view.assert_send_only_puzzle(gryffindor, game.levels[2])

    await check_key(key="SH3", **key_kwargs)
    expected_second_key = dto.KeyTime(
        text="SH3",
        type_=enums.KeyType.simple,
        is_duplicate=False,
        at=datetime.now(tz=tz_utc),
        level_number=2,
        player=harry,
        team=gryffindor,
    )
    dummy_view.assert_correct_key_only(expected_second_key)
    dummy_view.assert_game_finished_only(gryffindor)
    dummy_view.assert_game_finished_all({gryffindor})

    keys = await get_typed_keys(game=game, player=author, dao=check_dao.typed_keys)

    assert list(keys.keys()) == [gryffindor]
    assert len(keys[gryffindor]) == 2
    assert_time_key(expected_first_key, list(keys[gryffindor])[0])
    assert_time_key(expected_second_key, list(keys[gryffindor])[1])
    assert await dao.game_player.is_all_team_finished(game)
    assert GameStatus.finished == (await dao.game.get_by_id(game.id, author)).status
    dummy_view.assert_no_unchecked()
    dummy_org_notifier.assert_no_calls()


@pytest.mark.asyncio
async def test_cycle_play_routed_game(
    dao: HolderDao,
    locker: KeyCheckerFactory,
    check_dao: HolderDao,
    scheduler: SchedulerMock,
    author: dto.Player,
    harry: dto.Player,
    draco: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    started_routed_game: dto.FullGame,
):
    game = started_routed_game
    # delete slytherin from game
    await leave(draco, draco, dao.team_leaver)
    dummy_view = GameViewMock()
    dummy_log = GameLogWriterMock()

    dummy_org_notifier = OrgNotifierMock()
    orgs = await get_orgs(game, dao.organizer)
    key_kwargs = {
        "player": harry,
        "team": gryffindor,
        "input_container": MockInputContainer(),
        "game": game,
    }

    check_key = CheckKeyInteractor(
        dao=dao.game_player,
        view=dummy_view,
        game_log=dummy_log,
        org_notifier=dummy_org_notifier,
        locker=locker,
        scheduler=scheduler,
    )

    await check_key(key="SHTO3", **key_kwargs)
    expected_first_key = dto.KeyTime(
        text="SHTO3",
        type_=enums.KeyType.simple,
        is_duplicate=False,
        at=datetime.now(tz=tz_utc),
        level_number=0,
        player=harry,
        team=gryffindor,
    )
    dummy_view.assert_correct_key_only(expected_first_key)
    dummy_org_notifier.assert_one_event(
        LevelUp(team=gryffindor, new_level=game.levels[2], orgs_list=orgs)
    )
    dummy_view.assert_send_only_puzzle(gryffindor, game.levels[2])

    await check_key(key="SHTO1", **key_kwargs)
    expected_second_key = dto.KeyTime(
        text="SHTO1",
        type_=enums.KeyType.simple,
        is_duplicate=False,
        at=datetime.now(tz=tz_utc),
        level_number=2,
        player=harry,
        team=gryffindor,
    )
    dummy_view.assert_correct_key_only(expected_second_key)
    dummy_org_notifier.assert_one_event(
        LevelUp(team=gryffindor, new_level=game.levels[0], orgs_list=orgs)
    )
    dummy_view.assert_send_only_puzzle(gryffindor, game.levels[0])

    await check_key(key="SHTO3", **key_kwargs)
    expected_third_key = dto.KeyTime(
        text="SHTO3",
        type_=enums.KeyType.simple,
        is_duplicate=False,
        at=datetime.now(tz=tz_utc),
        level_number=0,
        player=harry,
        team=gryffindor,
    )
    dummy_view.assert_correct_key_only(expected_third_key)
    dummy_org_notifier.assert_one_event(
        LevelUp(team=gryffindor, new_level=game.levels[2], orgs_list=orgs)
    )
    dummy_view.assert_send_only_puzzle(gryffindor, game.levels[2])

    await check_key(key="SH3", **key_kwargs)
    expected_last_key = dto.KeyTime(
        text="SH3",
        type_=enums.KeyType.simple,
        is_duplicate=False,
        at=datetime.now(tz=tz_utc),
        level_number=2,
        player=harry,
        team=gryffindor,
    )
    dummy_view.assert_correct_key_only(expected_last_key)
    dummy_view.assert_game_finished_only(gryffindor)
    dummy_view.assert_game_finished_all({gryffindor})

    keys = await get_typed_keys(game=game, player=author, dao=check_dao.typed_keys)

    assert list(keys.keys()) == [gryffindor]
    assert len(keys[gryffindor]) == 4
    assert_time_key(expected_first_key, list(keys[gryffindor])[0])
    assert_time_key(expected_second_key, list(keys[gryffindor])[1])
    assert_time_key(expected_third_key, list(keys[gryffindor])[2])
    assert_time_key(expected_last_key, list(keys[gryffindor])[3])
    assert await dao.game_player.is_all_team_finished(game)
    assert GameStatus.finished == (await dao.game.get_by_id(game.id, author)).status
    dummy_view.assert_no_unchecked()
    dummy_org_notifier.assert_no_calls()


@pytest.mark.asyncio
async def test_get_current_hints(
    game_with_waivers: dto.FullGame,
    dishka_request: AsyncContainer,
    dao: HolderDao,
    author: dto.Player,
    harry: dto.Player,
    ron: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
):
    await leave(ron, ron, dao.team_leaver)
    level_time = models.LevelTime(
        game_id=game_with_waivers.id,
        team_id=gryffindor.id,
        level_number=0,
        start_at=datetime.now(tz=tz_utc) - timedelta(minutes=2),
    )
    dao.level_time._save(level_time)
    await dao.commit()
    interactor = await dishka_request.get(GamePlayReaderInteractor)
    hints = await interactor(hermione._user)
    hints_harry = await interactor(harry._user)
    assert len(hints.hints) == 2
    assert len(hints_harry.hints) == 2
    assert hints_harry.hints == hints.hints
    with pytest.raises(exceptions.PlayerNotInTeam):
        await interactor(ron._user)
    with suppress(exceptions.PlayerRestoredInTeam):
        await join_team(ron, gryffindor, harry, dao.team_player)
    with pytest.raises(exceptions.WaiverError):
        await interactor(ron._user)
