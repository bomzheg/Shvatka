from contextlib import suppress

import pytest

from app.dao.holder import HolderDao
from app.models import db, dto
from app.models.enums import GameStatus
from app.models.enums.played import Played
from app.services.player import join_to_team, leave
from app.services.waiver import get_voted_list, add_vote
from app.utils.exceptions import PlayerRestoredInTeam, WaiverForbidden
from tests.utils.player import create_hermi_player, create_harry_player
from tests.utils.team import create_first_team


@pytest.mark.asyncio
async def test_get_voted_list(dao: HolderDao):
    captain = await create_harry_player(dao)
    team = await create_first_team(captain, dao)
    player = await create_hermi_player(dao)
    game_db = db.Game(
        author_id=captain.id,
        name="good game",
        status=GameStatus.underconstruction,
    )
    dao.game._save(game_db)
    await dao.game.commit()
    game = dto.Game.from_db(game=game_db, author=captain)

    await join_to_team(player, team, dao.player_in_team)
    await add_vote(game, team, captain, Played.yes, dao)
    await add_vote(game, team, player, Played.yes, dao)

    actual = await get_voted_list(team, dao)
    assert len(actual) == 1
    actual_voted = actual[Played.yes]
    assert len(actual_voted) == 2

    await leave(player, dao.player_in_team)
    actual = await get_voted_list(team, dao)
    assert len(actual) == 1
    actual_voted = actual[Played.yes]
    assert len(actual_voted) == 1
    assert actual_voted[0].player.id == captain.id

    with suppress(PlayerRestoredInTeam):
        await join_to_team(player, team, dao.player_in_team)
    waiver = db.Waiver(
        player_id=player.id,
        team_id=team.id,
        game_id=game.id,
        role="123",
        played=Played.revoked,
    )
    dao.waiver._save(waiver)
    await dao.waiver.commit()
    with pytest.raises(WaiverForbidden):
        await add_vote(game, team, player, Played.yes, dao)
