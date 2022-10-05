import pytest
from dataclass_factory import Factory
from mockito import mock, when, ANY

from db.dao.holder import HolderDao
from shvatka.models.enums.played import Played
from shvatka.scheduler import Scheduler
from shvatka.services.game import start_waivers, upsert_game
from shvatka.services.game_play import start_game
from shvatka.services.player import join_team
from shvatka.services.waiver import add_vote, approve_waivers
from shvatka.views.game import GameView, GameLogWriter
from tests.mocks.aiogram_mocks import mock_coro
from tests.utils.player import create_promoted_harry, create_hermi_player
from tests.utils.team import create_first_team


@pytest.mark.asyncio
async def test_game_play(simple_scn: dict, dao: HolderDao, dcf: Factory):
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
    when(dummy_view).send_puzzle(team, ANY).thenReturn(mock_coro(None))
    dummy_log = mock(GameLogWriter)
    when(dummy_log).log("Game started").thenReturn(mock_coro(None))
    dummy_sched = mock(Scheduler)
    when(dummy_sched).plain_hint(game, team, 0, ANY).thenReturn(mock_coro(None))
    await start_game(game, dao.game_starter, dummy_log, dummy_view, dummy_sched)
    assert 1 == await dao.level_time.count()
