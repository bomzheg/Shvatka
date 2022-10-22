from datetime import datetime

import pytest
from dataclass_factory import Factory
from mockito import mock, when, ANY, unstub

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.models.enums.played import Played
from shvatka.scheduler import Scheduler
from shvatka.services.game import start_waivers, upsert_game
from shvatka.services.game_play import start_game, send_hint, check_key
from shvatka.services.game_stat import get_typed_keys
from shvatka.services.player import join_team
from shvatka.services.waiver import add_vote, approve_waivers
from shvatka.utils.key_checker_lock import KeyCheckerFactory
from shvatka.views.game import GameView, GameLogWriter, OrgNotifier, LevelUp
from tests.mocks.aiogram_mocks import mock_coro
from tests.utils.player import create_promoted_harry, create_hermi_player
from tests.utils.team import create_first_team
from tests.utils.time_key import assert_time_key


@pytest.mark.asyncio
async def test_game_play(
    simple_scn: dict, dao: HolderDao, dcf: Factory,
    locker: KeyCheckerFactory, check_dao: HolderDao, scheduler: Scheduler,
):
    captain = await create_promoted_harry(dao)
    team = await create_first_team(captain, dao)
    game = await upsert_game(simple_scn, captain, dao.game_upserter, dcf)
    await start_waivers(game, captain, dao.game)

    player = await create_hermi_player(dao)
    await join_team(player, team, dao.player_in_team)
    await add_vote(game, team, captain, Played.yes, dao.waiver_vote_adder)
    await add_vote(game, team, player, Played.yes, dao.waiver_vote_adder)
    await approve_waivers(game, team, captain, dao.waiver_approver)

    dummy_view = mock(GameView)
    when(dummy_view).send_puzzle(team, game.get_hint(0, 0)).thenReturn(mock_coro(None))
    dummy_log = mock(GameLogWriter)
    when(dummy_log).log("Game started").thenReturn(mock_coro(None))
    dummy_sched = mock(Scheduler)
    when(dummy_sched).plain_hint(game.levels[0], team, 1, ANY).thenReturn(mock_coro(None))
    await start_game(game, dao.game_starter, dummy_log, dummy_view, dummy_sched)
    assert 1 == await check_dao.level_time.count()

    when(dummy_view).send_hint(team, game.get_hint(0, 1)).thenReturn(mock_coro(None))
    when(dummy_sched).plain_hint(game.levels[0], team, 2, ANY).thenReturn(mock_coro(None))
    await send_hint(
        level=game.levels[0], hint_number=1, team=team,
        dao=dao.level_time, view=dummy_view, scheduler=dummy_sched,
    )

    dummy_org_notifier = mock(OrgNotifier)
    key_kwargs = dict(
        player=captain, team=team, game=game, dao=dao.key_checker, view=dummy_view,
        game_log=dummy_log, org_notifier=dummy_org_notifier, locker=locker, scheduler=scheduler,
    )
    when(dummy_view).wrong_key(key=ANY).thenReturn(mock_coro(None))
    await check_key(key="SHWRONG", **key_kwargs)
    keys = await get_typed_keys(game, check_dao.key_time)

    assert [team] == list(keys.keys())
    assert 1 == len(keys[team])
    assert_time_key(
        dto.KeyTime(
            text="SHWRONG", is_correct=False, is_duplicate=False,
            at=datetime.utcnow(), level_number=0, player=captain,
        ),
        list(keys[team])[0]
    )

    when(dummy_view).correct_key(key=ANY).thenReturn(mock_coro(None))
    await check_key(key="SH123", **key_kwargs)

    when(dummy_view).duplicate_key(key=ANY).thenReturn(mock_coro(None))
    await check_key(key="SH123", **key_kwargs)

    unstub(dummy_view)
    when(dummy_view).correct_key(key=ANY).thenReturn(mock_coro(None))
    when(dummy_view).send_puzzle(team=team, puzzle=game.get_hint(1, 0))\
        .thenReturn(mock_coro(None))
    when(dummy_org_notifier).notify(LevelUp(team=team, new_level=game.levels[1]))\
        .thenReturn(mock_coro(None))
    await check_key(key="SH321", **key_kwargs)
    keys = await get_typed_keys(game, check_dao.key_time)

    assert [team] == list(keys.keys())
    assert 4 == len(keys[team])
    assert_time_key(
        dto.KeyTime(
            text="SHWRONG", is_correct=False, is_duplicate=False,
            at=datetime.utcnow(), level_number=0, player=captain,
        ),
        list(keys[team])[0]
    )
    assert_time_key(
        dto.KeyTime(
            text="SH123", is_correct=True, is_duplicate=False,
            at=datetime.utcnow(), level_number=0, player=captain,
        ),
        list(keys[team])[1]
    )
    assert_time_key(
        dto.KeyTime(
            text="SH123", is_correct=True, is_duplicate=True,
            at=datetime.utcnow(), level_number=0, player=captain,
        ),
        list(keys[team])[2]
    )
    assert_time_key(
        dto.KeyTime(
            text="SH321", is_correct=True, is_duplicate=False,
            at=datetime.utcnow(), level_number=0, player=captain,
        ),
        list(keys[team])[3]
    )
