import pytest
from httpx import AsyncClient

from shvatka.core.models import dto
from shvatka.core.models.enums.played import Played
from shvatka.core.players.player import join_team
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.api.dependencies.auth import AuthProperties
from shvatka.api.models.auth import Token
from tests.mocks.team_notifier import TeamNotifierMock


def auth_cookies(token: Token) -> dict[str, str]:
    return {"Authorization": f"{token.token_type} {token.access_token}"}


@pytest.fixture
def token(harry: dto.Player, auth: AuthProperties) -> Token:
    return auth.create_user_token(harry)


@pytest.mark.asyncio
async def test_replace_current_waivers(
    client: AsyncClient,
    harry: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    game: dto.FullGame,
    token: Token,
    dao: HolderDao,
    check_dao: HolderDao,
):
    await join_team(hermione, gryffindor, harry, dao.team_player, notifier=TeamNotifierMock())
    await dao.game.start_waivers(game)
    await dao.commit()

    resp = await client.put(
        "/waivers/game/current",
        cookies=auth_cookies(token),
        json={
            "waivers": [
                {"player_id": harry.id, "played": Played.yes.name},
                {"player_id": hermione.id, "played": Played.no.name},
            ]
        },
        follow_redirects=True,
    )
    assert resp.is_success
    resp.read()
    body = resp.json()
    assert body["team"]["id"] == gryffindor.id
    by_player = {p["player"]["id"]: p["played"] for p in body["players"]}
    assert by_player == {harry.id: Played.yes.name, hermione.id: Played.no.name}

    assert (await check_dao.waiver.get_player_waiver(game, harry, gryffindor)).played == Played.yes
    assert (
        await check_dao.waiver.get_player_waiver(game, hermione, gryffindor)
    ).played == Played.no


@pytest.mark.asyncio
async def test_replace_current_waivers_removes_absent(
    client: AsyncClient,
    harry: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    game: dto.FullGame,
    token: Token,
    dao: HolderDao,
    check_dao: HolderDao,
):
    await join_team(hermione, gryffindor, harry, dao.team_player, notifier=TeamNotifierMock())
    await dao.game.start_waivers(game)
    await dao.waiver.upsert(
        dto.Waiver(player=hermione, team=gryffindor, game=game, played=Played.yes)
    )
    await dao.commit()

    resp = await client.put(
        "/waivers/game/current",
        cookies=auth_cookies(token),
        json={"waivers": [{"player_id": harry.id, "played": Played.yes.name}]},
        follow_redirects=True,
    )
    assert resp.is_success
    resp.read()
    by_player = {p["player"]["id"] for p in resp.json()["players"]}
    assert by_player == {harry.id}
    # hermione's waiver must be gone after replace
    assert await check_dao.waiver.get_player_waiver(game, hermione, gryffindor) is None


@pytest.mark.asyncio
async def test_replace_current_waivers_forbidden_for_non_captain(
    client: AsyncClient,
    harry: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    game: dto.FullGame,
    auth: AuthProperties,
    dao: HolderDao,
):
    await join_team(hermione, gryffindor, harry, dao.team_player, notifier=TeamNotifierMock())
    await dao.game.start_waivers(game)
    await dao.commit()
    hermione_token = auth.create_user_token(hermione)

    resp = await client.put(
        "/waivers/game/current",
        cookies=auth_cookies(hermione_token),
        json={"waivers": [{"player_id": hermione.id, "played": Played.yes.name}]},
        follow_redirects=True,
    )
    assert resp.status_code == 422  # PermissionsError -> SHError


@pytest.mark.asyncio
async def test_get_waivers_by_game(
    client: AsyncClient,
    harry: dto.Player,
    gryffindor: dto.Team,
    game: dto.FullGame,
    dao: HolderDao,
):
    await dao.waiver.upsert(
        dto.Waiver(player=harry, team=gryffindor, game=game, played=Played.yes)
    )
    await dao.commit()

    resp = await client.get(f"/waivers/game/{game.id}")
    assert resp.is_success
    resp.read()
    body = resp.json()
    assert gryffindor.id in [team["id"] for team in body["teams"]]
    voted = body["waivers"][str(gryffindor.id)]
    assert harry.id in [p["player"]["id"] for p in voted]


@pytest.mark.asyncio
async def test_get_waivers_by_unknown_game(client: AsyncClient):
    resp = await client.get("/waivers/game/99999999")
    assert resp.status_code == 404
