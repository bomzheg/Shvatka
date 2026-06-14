import pytest
from dataclass_factory import Factory
from httpx import AsyncClient

from shvatka.api.models import responses
from shvatka.api.models.auth import Token
from shvatka.core.models import dto
from shvatka.core.models import enums
from shvatka.core.players.player import get_full_team_player, join_team
from shvatka.core.utils.defaults_constants import CAPTAIN_ROLE
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.api.dependencies.auth import AuthProperties
from tests.fixtures.chat_constants import create_gryffindor_dto_chat
from tests.fixtures.team import create_team_
from tests.mocks.game_log import GameLogWriterMock
from tests.mocks.team_notifier import TeamNotifierMock


@pytest.fixture
def token(harry: dto.Player, auth: AuthProperties) -> Token:
    return auth.create_user_token(harry)


def auth_cookies(token: Token) -> dict[str, str]:
    return {"Authorization": f"{token.token_type} {token.access_token}"}


@pytest.mark.asyncio
async def test_get_team(
    client: AsyncClient,
    harry: dto.Player,
    token: Token,
    dao: HolderDao,
    game_log: GameLogWriterMock,
):
    team = await create_team_(harry, create_gryffindor_dto_chat(), dao, game_log)
    resp = await client.get(
        "/teams/my",
        cookies=auth_cookies(token),
        follow_redirects=True,
    )
    assert resp.is_success
    dcf = Factory()
    resp.read()
    assert responses.Team.from_core(team) == dcf.load(resp.json(), responses.Team)


@pytest.mark.asyncio
async def test_get_all_teams(
    client: AsyncClient,
    gryffindor: dto.Team,
):
    resp = await client.get("/teams")
    assert resp.is_success
    resp.read()
    items = resp.json()["items"]
    assert gryffindor.id in [team["id"] for team in items]


@pytest.mark.asyncio
async def test_get_team_by_id(
    client: AsyncClient,
    gryffindor: dto.Team,
):
    resp = await client.get(f"/teams/{gryffindor.id}")
    assert resp.is_success
    resp.read()
    body = resp.json()
    assert body["id"] == gryffindor.id
    assert body["name"] == gryffindor.name
    assert body["captain"]["id"] == gryffindor.captain.id


@pytest.mark.asyncio
async def test_get_team_players(
    client: AsyncClient,
    harry: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    dao: HolderDao,
):
    await join_team(hermione, gryffindor, harry, dao.team_player, notifier=TeamNotifierMock())
    resp = await client.get(f"/teams/{gryffindor.id}/players")
    assert resp.is_success
    resp.read()
    items = resp.json()["items"]
    by_player = {item["id"]: item for item in items}
    assert harry.id in by_player
    assert hermione.id in by_player
    assert by_player[harry.id]["role"] == CAPTAIN_ROLE
    assert "permissions" in by_player[hermione.id]
    assert by_player[hermione.id]["date_joined"] is not None


@pytest.mark.asyncio
async def test_add_player_to_my_team(
    client: AsyncClient,
    harry: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    token: Token,
    check_dao: HolderDao,
):
    resp = await client.post(
        f"/teams/{gryffindor.id}/players",
        cookies=auth_cookies(token),
        json={"player_id": hermione.id, "role": "seeker", "emoji": "🧹"},
        follow_redirects=True,
    )
    assert resp.is_success
    resp.read()
    body = resp.json()
    assert body["id"] == hermione.id
    assert body["role"] == "seeker"
    assert body["emoji"] == "🧹"
    actual = await get_full_team_player(hermione, gryffindor, check_dao.team_player)
    assert actual.role == "seeker"
    assert actual.emoji == "🧹"


@pytest.mark.asyncio
async def test_add_player_forbidden_for_non_captain(
    client: AsyncClient,
    harry: dto.Player,
    hermione: dto.Player,
    draco: dto.Player,
    gryffindor: dto.Team,
    auth: AuthProperties,
    dao: HolderDao,
):
    await join_team(hermione, gryffindor, harry, dao.team_player, notifier=TeamNotifierMock())
    hermione_token = auth.create_user_token(hermione)
    resp = await client.post(
        f"/teams/{gryffindor.id}/players",
        cookies=auth_cookies(hermione_token),
        json={"player_id": draco.id},
        follow_redirects=True,
    )
    assert resp.status_code == 422  # PermissionsError -> SHError


@pytest.mark.asyncio
async def test_update_team_player(
    client: AsyncClient,
    harry: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    token: Token,
    dao: HolderDao,
    check_dao: HolderDao,
):
    await join_team(hermione, gryffindor, harry, dao.team_player, notifier=TeamNotifierMock())
    resp = await client.put(
        f"/teams/{gryffindor.id}/players/{hermione.id}",
        cookies=auth_cookies(token),
        json={
            "role": "keeper",
            "emoji": "🥅",
            "permissions": {enums.TeamPlayerPermission.can_change_team_name.name: True},
        },
        follow_redirects=True,
    )
    assert resp.is_success
    resp.read()
    body = resp.json()
    assert body["role"] == "keeper"
    assert body["emoji"] == "🥅"
    assert body["permissions"][enums.TeamPlayerPermission.can_change_team_name.name] is True
    actual = await get_full_team_player(hermione, gryffindor, check_dao.team_player)
    assert actual.role == "keeper"
    assert actual.can_change_team_name


@pytest.mark.asyncio
async def test_remove_player_from_team(
    client: AsyncClient,
    harry: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    token: Token,
    dao: HolderDao,
    check_dao: HolderDao,
):
    await join_team(hermione, gryffindor, harry, dao.team_player, notifier=TeamNotifierMock())
    resp = await client.request(
        "DELETE",
        f"/teams/{gryffindor.id}/players/{hermione.id}",
        cookies=auth_cookies(token),
        follow_redirects=True,
    )
    assert resp.status_code == 204
    assert await check_dao.team_player.get_team(hermione) is None


@pytest.mark.asyncio
async def test_edit_team(
    client: AsyncClient,
    harry: dto.Player,
    gryffindor: dto.Team,
    token: Token,
    check_dao: HolderDao,
):
    resp = await client.put(
        f"/teams/{gryffindor.id}",
        cookies=auth_cookies(token),
        json={"name": "New Gryffindor", "description": "best team"},
        follow_redirects=True,
    )
    assert resp.is_success
    resp.read()
    body = resp.json()
    assert body["name"] == "New Gryffindor"
    assert body["description"] == "best team"
    actual = await check_dao.team.get_by_id(gryffindor.id)
    assert actual.name == "New Gryffindor"
    assert actual.description == "best team"
