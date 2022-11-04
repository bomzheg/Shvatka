from datetime import datetime, timedelta

import pytest
from dataclass_factory import Factory
from mockito import mock, when, ANY, unstub

from db import models
from db.dao.holder import HolderDao
from shvatka.clients.file_storage import FileStorage
from shvatka.models import dto
from shvatka.models.enums import GameStatus
from shvatka.models.enums.played import Played
from shvatka.scheduler import Scheduler
from shvatka.services.game import start_waivers, upsert_game
from shvatka.services.game_play import start_game, send_hint, check_key, get_available_hints
from shvatka.services.game_stat import get_typed_keys
from shvatka.services.player import join_team
from shvatka.services.waiver import add_vote, approve_waivers
from shvatka.utils.key_checker_lock import KeyCheckerFactory
from shvatka.views.game import GameView, GameLogWriter, OrgNotifier, LevelUp
from tests.mocks.aiogram_mocks import mock_coro
from tests.utils.time_key import assert_time_key


@pytest.mark.asyncio
async def test_game_play(
    simple_scn: dict, dao: HolderDao, dcf: Factory, file_storage: FileStorage,
    locker: KeyCheckerFactory, check_dao: HolderDao, scheduler: Scheduler,
    author: dto.Player, harry: dto.Player, hermione: dto.Player,
    gryffindor: dto.Team,
):
    game = await upsert_game(simple_scn, {}, author, dao.game_upserter, dcf, file_storage)
    await start_waivers(game, author, dao.game)

    await join_team(hermione, gryffindor, dao.player_in_team)
    await add_vote(game, gryffindor, harry, Played.yes, dao.waiver_vote_adder)
    await add_vote(game, gryffindor, hermione, Played.yes, dao.waiver_vote_adder)
    await approve_waivers(game, gryffindor, harry, dao.waiver_approver)

    dummy_view = mock(GameView)
    when(dummy_view).send_puzzle(gryffindor, game.get_hint(0, 0), game.levels[0]).thenReturn(mock_coro(None))
    dummy_log = mock(GameLogWriter)
    when(dummy_log).log("Game started").thenReturn(mock_coro(None))
    dummy_sched = mock(Scheduler)
    when(dummy_sched).plain_hint(level=game.levels[0], team=(gryffindor), hint_number=1, run_at=ANY).thenReturn(
        mock_coro(None))
    await start_game(game, dao.game_starter, dummy_log, dummy_view, dummy_sched)
    assert 1 == await check_dao.level_time.count()

    when(dummy_view).send_hint(gryffindor, 1, game.levels[0]).thenReturn(mock_coro(None))
    when(dummy_sched).plain_hint(game.levels[0], gryffindor, 2, ANY).thenReturn(mock_coro(None))
    await send_hint(
        level=game.levels[0], hint_number=1, team=gryffindor,
        dao=dao.level_time, view=dummy_view, scheduler=dummy_sched,
    )

    dummy_org_notifier = mock(OrgNotifier)
    key_kwargs = dict(
        player=harry, team=gryffindor, game=game, dao=dao.game_player, view=dummy_view,
        game_log=dummy_log, org_notifier=dummy_org_notifier, locker=locker, scheduler=scheduler,
    )
    when(dummy_view).wrong_key(key=ANY).thenReturn(mock_coro(None))
    await check_key(key="SHWRONG", **key_kwargs)
    keys = await get_typed_keys(game, check_dao.key_time)

    assert [gryffindor] == list(keys.keys())
    assert 1 == len(keys[gryffindor])
    assert_time_key(
        dto.KeyTime(
            text="SHWRONG", is_correct=False, is_duplicate=False,
            at=datetime.utcnow(), level_number=0, player=harry, team=gryffindor,
        ),
        list(keys[gryffindor])[0]
    )

    when(dummy_view).correct_key(key=ANY).thenReturn(mock_coro(None))
    await check_key(key="SH123", **key_kwargs)

    when(dummy_view).duplicate_key(key=ANY).thenReturn(mock_coro(None))
    await check_key(key="SH123", **key_kwargs)

    unstub(dummy_view)
    when(dummy_view).correct_key(key=ANY).thenReturn(mock_coro(None))
    when(dummy_view).send_puzzle(team=gryffindor, puzzle=game.get_hint(1, 0), level=game.levels[1]) \
        .thenReturn(mock_coro(None))
    when(dummy_org_notifier).notify(LevelUp(team=gryffindor, new_level=game.levels[1])) \
        .thenReturn(mock_coro(None))
    await check_key(key="SH321", **key_kwargs)

    unstub(dummy_view)
    dummy_view = mock(GameView)
    when(dummy_log).log("Game finished").thenReturn(mock_coro(None))
    when(dummy_org_notifier).notify(LevelUp(team=gryffindor, new_level=game.levels[1])) \
        .thenReturn(mock_coro(None))
    when(dummy_view).correct_key(key=ANY).thenReturn(mock_coro(None))
    when(dummy_view).game_finished(gryffindor).thenReturn(mock_coro(None))
    when(dummy_view).game_finished_by_all(gryffindor).thenReturn(mock_coro(None))
    key_kwargs["view"] = dummy_view
    await check_key(key="SHOOT", **key_kwargs)

    keys = await get_typed_keys(game, check_dao.key_time)

    assert [gryffindor] == list(keys.keys())
    assert 5 == len(keys[gryffindor])
    assert_time_key(
        dto.KeyTime(
            text="SHWRONG", is_correct=False, is_duplicate=False,
            at=datetime.utcnow(), level_number=0, player=harry, team=gryffindor,
        ),
        list(keys[gryffindor])[0]
    )
    assert_time_key(
        dto.KeyTime(
            text="SH123", is_correct=True, is_duplicate=False,
            at=datetime.utcnow(), level_number=0, player=harry, team=gryffindor,
        ),
        list(keys[gryffindor])[1]
    )
    assert_time_key(
        dto.KeyTime(
            text="SH123", is_correct=True, is_duplicate=True,
            at=datetime.utcnow(), level_number=0, player=harry, team=gryffindor,
        ),
        list(keys[gryffindor])[2]
    )
    assert_time_key(
        dto.KeyTime(
            text="SH321", is_correct=True, is_duplicate=False,
            at=datetime.utcnow(), level_number=0, player=harry, team=gryffindor,
        ),
        list(keys[gryffindor])[3]
    )
    assert_time_key(
        dto.KeyTime(
            text="SHOOT", is_correct=True, is_duplicate=False,
            at=datetime.utcnow(), level_number=0, player=harry, team=gryffindor,
        ),
        list(keys[gryffindor])[4]
    )
    assert await dao.game_player.is_all_team_finished(game)
    assert GameStatus.finished == (await dao.game.get_by_id(game.id, harry)).status


@pytest.mark.asyncio
async def test_get_current_hints(
    simple_scn: dict, dao: HolderDao, dcf: Factory, locker: KeyCheckerFactory, file_storage: FileStorage,
    author: dto.Player, harry: dto.Player, hermione: dto.Player,
    gryffindor: dto.Team,
):
    game = await upsert_game(simple_scn, {}, author, dao.game_upserter, dcf, file_storage)
    await start_waivers(game, author, dao.game)

    await join_team(hermione, gryffindor, dao.player_in_team)
    await add_vote(game, gryffindor, harry, Played.yes, dao.waiver_vote_adder)
    await add_vote(game, gryffindor, hermione, Played.yes, dao.waiver_vote_adder)
    await approve_waivers(game, gryffindor, harry, dao.waiver_approver)
    level_time = models.LevelTime(
        game_id=game.id,
        team_id=gryffindor.id,
        level_number=0,
        start_at=datetime.utcnow() - timedelta(minutes=1),
    )
    dao.level_time._save(level_time)
    await dao.commit()
    actual_hints = await get_available_hints(game, gryffindor, dao.game_player)
    assert len(actual_hints) == 2

