import pytest

from shvatka.core.services.chat import upsert_chat
from shvatka.core.players.player import get_full_team_player, upsert_player
from shvatka.core.services.team import change_chat, create_team, get_by_chat
from shvatka.core.services.user import upsert_user
from shvatka.core.teams.interactors import CreateTeamInteractor
from shvatka.core.views.game import GameLogWriter
from shvatka.infrastructure.db.dao.complex.team import TeamCreatorImpl
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.chat_constants import create_gryffindor_dto_chat
from tests.fixtures.identity import MockIdentityProvider
from tests.fixtures.player import promote
from tests.fixtures.user_constants import create_dto_harry


@pytest.mark.asyncio
async def test_save_team(dao: HolderDao, game_log: GameLogWriter):
    chat = await upsert_chat(create_gryffindor_dto_chat(), dao.chat)
    user = await upsert_user(create_dto_harry(), dao.user)
    player = await upsert_player(user, dao.player)
    await promote(player, dao)
    team = await create_team(chat, player, dao.team_creator, game_log)
    assert team.id is not None
    assert team.name == chat.name


@pytest.mark.asyncio
async def test_get_team(dao: HolderDao, game_log: GameLogWriter):
    chat = await upsert_chat(create_gryffindor_dto_chat(), dao.chat)
    assert await get_by_chat(chat, dao.team) is None

    await test_save_team(dao, game_log)

    team = await get_by_chat(chat, dao.team)
    assert team is not None
    assert team.id is not None
    assert team.name == chat.title


@pytest.mark.asyncio
async def test_save_team_no_chat(dao: HolderDao, game_log: GameLogWriter):
    user = await upsert_user(create_dto_harry(), dao.user)
    player = await upsert_player(user, dao.player)
    await promote(player, dao)
    interactor = CreateTeamInteractor(dao=TeamCreatorImpl(dao=dao), game_log=game_log)
    team = await interactor(
        identity=MockIdentityProvider(player=player),
        name="Web team",
        description="plays only via web",
    )
    assert team.id is not None
    assert team.name == "Web team"
    assert not team.has_chat()
    assert team.get_chat_id() is None
    assert not team.is_dummy
    saved = await dao.team.get_by_id(team.id)
    assert not saved.has_chat()


@pytest.mark.asyncio
async def test_link_chat_to_team_without_chat(dao: HolderDao, game_log: GameLogWriter):
    """The captain's bridge "move team to another chat" flow must also work
    when the team has no chat yet: it links the team to its first chat."""
    user = await upsert_user(create_dto_harry(), dao.user)
    player = await upsert_player(user, dao.player)
    await promote(player, dao)
    interactor = CreateTeamInteractor(dao=TeamCreatorImpl(dao=dao), game_log=game_log)
    team = await interactor(identity=MockIdentityProvider(player=player), name="Web team")
    chat = await upsert_chat(create_gryffindor_dto_chat(), dao.chat)
    captain = await get_full_team_player(player, team, dao.team_player)
    await change_chat(team, captain, chat, dao.chat)
    saved = await dao.team.get_by_id(team.id)
    assert saved.has_chat()
    assert saved.get_chat_id() == chat.tg_id
    assert await get_by_chat(chat, dao.team) == team
