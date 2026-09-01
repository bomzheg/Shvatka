from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.exc import NoResultFound

from shvatka.api.app.dependencies.auth import AuthProperties
from shvatka.api.auth.responses import Token
from shvatka.core.models import dto
from shvatka.core.models.enums import GameStatus
from shvatka.core.models.enums.played import Played
from shvatka.core.players.player import upsert_player
from shvatka.core.services.user import upsert_user
from shvatka.core.utils.defaults_constants import DEFAULT_ROLE
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.scn_fixtures import GUID
from tests.fixtures.user_constants import (
    create_dto_draco,
    create_dto_hermione,
    create_dto_ron,
)
from tests.mocks.scheduler_mock import SchedulerMock

GAME_START_AT = datetime(2025, 4, 12, 16, 0, tzinfo=UTC)

# Scenario body for PUT /admin/games/{id}/scenario.
ADMIN_SCENARIO: dict = {
    "name": "admin edited game",
    "__model_version__": 1,
    "files": [],
    "levels": [
        {
            "id": "first",
            "__model_version__": 1,
            "conditions": [{"type": "WIN_KEY", "keys": ["SH123"]}],
            "time_hints": [
                {"time": 0, "hint": [{"type": "text", "text": "загадка"}]},
            ],
        },
    ],
}


def auth_cookies(token: Token) -> dict[str, str]:
    return {"Authorization": f"{token.token_type} {token.access_token}"}


async def complete_game(game: dto.FullGame, dao: HolderDao) -> None:
    """Bring a freshly built game to the ``complete`` status (uneditable by author)."""
    await dao.game.set_number(game, await dao.game.get_max_number() + 1)
    await dao.game.set_completed(game)
    await dao.commit()


@pytest_asyncio.fixture
async def hermione(dao: HolderDao) -> dto.Player:
    # tg_id 13 — deliberately not in the configured superusers list
    user_ = await upsert_user(create_dto_hermione(), dao.user)
    return await upsert_player(user_, dao.player)


@pytest.fixture
def admin_token(harry: dto.Player, auth: AuthProperties) -> Token:
    return auth.create_user_token(harry)


@pytest.fixture
def hermione_token(hermione: dto.Player, auth: AuthProperties) -> Token:
    return auth.create_user_token(hermione)


@pytest.mark.asyncio
async def test_admin_endpoint_forbidden_for_non_superuser(
    client: AsyncClient, hermione_token: Token
):
    resp = await client.get(
        "/admin/players",
        cookies=auth_cookies(hermione_token),
        follow_redirects=True,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_interactor_forbidden_for_non_superuser(
    client: AsyncClient, hermione_token: Token, hermione: dto.Player
):
    # this route self-checks inside the interactor (no route-level guard)
    resp = await client.put(
        f"/admin/players/{hermione.id}/email",
        json={"email": "x@example.org", "verified": True},
        cookies=auth_cookies(hermione_token),
        follow_redirects=True,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_users_me_is_admin_flag(
    client: AsyncClient, admin_token: Token, hermione_token: Token
):
    admin_resp = await client.get(
        "/users/me", cookies=auth_cookies(admin_token), follow_redirects=True
    )
    assert admin_resp.json()["is_admin"] is True
    plain_resp = await client.get(
        "/users/me", cookies=auth_cookies(hermione_token), follow_redirects=True
    )
    assert plain_resp.json()["is_admin"] is False


@pytest.mark.asyncio
async def test_list_players(
    client: AsyncClient, admin_token: Token, harry: dto.Player, hermione: dto.Player
):
    resp = await client.get(
        "/admin/players",
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success
    ids = {item["id"] for item in resp.json()["items"]}
    assert harry.id in ids
    assert hermione.id in ids


@pytest.mark.asyncio
async def test_list_players_filter_can_be_author(
    client: AsyncClient, admin_token: Token, harry: dto.Player, hermione: dto.Player
):
    resp = await client.get(
        "/admin/players",
        params={"can_be_author": True},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success
    ids = {item["id"] for item in resp.json()["items"]}
    assert harry.id in ids  # harry is promoted
    assert hermione.id not in ids  # hermione is not


@pytest.mark.asyncio
async def test_create_one_time_link(client: AsyncClient, admin_token: Token, hermione: dto.Player):
    resp = await client.post(
        f"/admin/players/{hermione.id}/one-time-link",
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success
    assert "/auth/one-time-token?token=" in resp.json()["url"]


@pytest.mark.asyncio
async def test_change_email_verified(
    client: AsyncClient,
    admin_token: Token,
    hermione: dto.Player,
    check_dao: HolderDao,
):
    resp = await client.put(
        f"/admin/players/{hermione.id}/email",
        json={"email": "hermione@example.org", "verified": True},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success
    body = resp.json()
    assert body["email"] == "hermione@example.org"
    assert body["is_verified"] is True
    stored = await check_dao.email.get_by_player_id(hermione.id)
    assert stored is not None
    assert stored.email == "hermione@example.org"
    assert stored.is_verified is True


@pytest.mark.asyncio
async def test_change_email_unverified(
    client: AsyncClient,
    admin_token: Token,
    hermione: dto.Player,
    check_dao: HolderDao,
):
    resp = await client.put(
        f"/admin/players/{hermione.id}/email",
        json={"email": "hermione2@example.org", "verified": False},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success
    assert resp.json()["is_verified"] is False
    stored = await check_dao.email.get_by_player_id(hermione.id)
    assert stored is not None
    assert stored.is_verified is False


@pytest.mark.asyncio
async def test_change_tg(
    client: AsyncClient,
    admin_token: Token,
    hermione: dto.Player,
    check_dao: HolderDao,
):
    new_tg_id = 555_000_111
    resp = await client.put(
        f"/admin/players/{hermione.id}/tg",
        json={"tg_id": new_tg_id, "username": "new_hermione", "first_name": "Herm"},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success
    assert resp.json()["tg"]["tg_id"] == new_tg_id
    reloaded = await check_dao.player.get_by_id(hermione.id)
    assert reloaded.get_chat_id() == new_tg_id


@pytest.mark.asyncio
async def test_change_tg_conflict(
    client: AsyncClient,
    admin_token: Token,
    harry: dto.Player,
    hermione: dto.Player,
):
    # harry's tg is already linked to harry; linking it to hermione must conflict
    resp = await client.put(
        f"/admin/players/{hermione.id}/tg",
        json={"tg_id": harry.get_chat_id()},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_change_username(
    client: AsyncClient,
    admin_token: Token,
    hermione: dto.Player,
    check_dao: HolderDao,
):
    resp = await client.put(
        f"/admin/players/{hermione.id}/username",
        json={"username": "granger"},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success
    assert resp.json()["username"] == "granger"
    reloaded = await check_dao.player.get_by_id(hermione.id)
    assert reloaded.username == "granger"


@pytest.mark.asyncio
async def test_change_username_invalid(
    client: AsyncClient,
    admin_token: Token,
    hermione: dto.Player,
    check_dao: HolderDao,
):
    before = (await check_dao.player.get_by_id(hermione.id)).username
    resp = await client.put(
        f"/admin/players/{hermione.id}/username",
        json={"username": "не латиница"},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 422
    assert (await check_dao.player.get_by_id(hermione.id)).username == before


@pytest.mark.asyncio
async def test_change_username_occupied(
    client: AsyncClient,
    admin_token: Token,
    harry: dto.Player,
    hermione: dto.Player,
    check_dao: HolderDao,
):
    harry_username = (await check_dao.player.get_by_id(harry.id)).username
    assert harry_username is not None
    resp = await client.put(
        f"/admin/players/{hermione.id}/username",
        json={"username": harry_username},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_change_own_username_to_the_same_one(
    client: AsyncClient,
    admin_token: Token,
    hermione: dto.Player,
    check_dao: HolderDao,
):
    """Keeping a player's current username must not trip the occupied check."""
    current = (await check_dao.player.get_by_id(hermione.id)).username
    assert current is not None
    resp = await client.put(
        f"/admin/players/{hermione.id}/username",
        json={"username": current},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success
    assert resp.json()["username"] == current


@pytest.mark.asyncio
async def test_change_username_forbidden_for_non_superuser(
    client: AsyncClient, hermione_token: Token, hermione: dto.Player
):
    resp = await client.put(
        f"/admin/players/{hermione.id}/username",
        json={"username": "granger"},
        cookies=auth_cookies(hermione_token),
        follow_redirects=True,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_poll_empty(client: AsyncClient, admin_token: Token):
    resp = await client.get(
        "/admin/poll",
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success
    assert resp.json() == {"teams": []}


@pytest.mark.asyncio
async def test_remove_poll_vote(client: AsyncClient, admin_token: Token, hermione: dto.Player):
    resp = await client.delete(
        f"/admin/poll/1/players/{hermione.id}",
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_merge_players(
    client: AsyncClient, admin_token: Token, dao: HolderDao, check_dao: HolderDao
):
    primary = await upsert_player(await upsert_user(create_dto_ron(), dao.user), dao.player)
    # secondary must have no telegram account; a dummy player fits and, unlike a
    # forum player, leaves no forum_users row for clear_data to trip over
    secondary = await dao.player.upsert_author_dummy()
    await dao.commit()

    resp = await client.post(
        "/admin/players/merge",
        json={"primary_id": primary.id, "secondary_id": secondary.id},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success, resp.text
    assert resp.json()["id"] == primary.id
    assert (await check_dao.player.get_by_id(primary.id)).id == primary.id
    with pytest.raises(NoResultFound):
        await check_dao.player.get_by_id(secondary.id)


@pytest.mark.asyncio
async def test_merge_players_same_id_rejected(
    client: AsyncClient, admin_token: Token, hermione: dto.Player
):
    resp = await client.post(
        "/admin/players/merge",
        json={"primary_id": hermione.id, "secondary_id": hermione.id},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_player_waiver_points(
    client: AsyncClient,
    admin_token: Token,
    dao: HolderDao,
    game: dto.FullGame,
    gryffindor: dto.Team,
    hermione: dto.Player,
):
    await dao.game.set_start_at(game, GAME_START_AT)
    await dao.waiver.upsert(
        dto.Waiver(player=hermione, team=gryffindor, game=game, played=Played.yes)
    )
    await dao.commit()

    resp = await client.get(
        f"/admin/players/{hermione.id}/waiver-points",
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success, resp.text
    items = resp.json()["items"]
    assert len(items) == 1
    point = items[0]
    assert point["game"]["id"] == game.id
    assert point["team"]["id"] == gryffindor.id
    assert datetime.fromisoformat(point["at_since"]) == GAME_START_AT - timedelta(hours=1)
    assert datetime.fromisoformat(point["at_until"]) == GAME_START_AT + timedelta(hours=48)


@pytest.mark.asyncio
async def test_get_player_waiver_points_forbidden_for_non_superuser(
    client: AsyncClient, hermione_token: Token, hermione: dto.Player
):
    resp = await client.get(
        f"/admin/players/{hermione.id}/waiver-points",
        cookies=auth_cookies(hermione_token),
        follow_redirects=True,
    )
    assert resp.status_code == 403


async def prepare_incompatible_players(
    dao: HolderDao,
    game: dto.FullGame,
    gryffindor: dto.Team,
    slytherin: dto.Team,
) -> tuple[dto.Player, dto.Player]:
    """Primary (tg) and secondary (dummy) with overlapping current memberships.

    The secondary played the game as a member of slytherin, so a waiver pins
    them to that team around the game start date.
    """
    await dao.game.set_start_at(game, GAME_START_AT)
    primary = await upsert_player(await upsert_user(create_dto_ron(), dao.user), dao.player)
    secondary = await dao.player.upsert_author_dummy()
    await dao.team_player.join_team(
        primary, gryffindor, role=DEFAULT_ROLE, joined_at=GAME_START_AT + timedelta(days=30)
    )
    await dao.team_player.join_team(
        secondary, slytherin, role=DEFAULT_ROLE, joined_at=GAME_START_AT - timedelta(days=30)
    )
    await dao.waiver.upsert(
        dto.Waiver(player=secondary, team=slytherin, game=game, played=Played.yes)
    )
    await dao.commit()
    return primary, secondary


@pytest.mark.asyncio
async def test_merge_players_incompatible_history_rejected(
    client: AsyncClient,
    admin_token: Token,
    dao: HolderDao,
    game: dto.FullGame,
    gryffindor: dto.Team,
    slytherin: dto.Team,
):
    primary, secondary = await prepare_incompatible_players(dao, game, gryffindor, slytherin)

    resp = await client.post(
        "/admin/players/merge",
        json={"primary_id": primary.id, "secondary_id": secondary.id},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 422
    assert resp.json()["type"] == "MergeError"


@pytest.mark.asyncio
async def test_merge_players_with_timeline(
    client: AsyncClient,
    admin_token: Token,
    dao: HolderDao,
    check_dao: HolderDao,
    game: dto.FullGame,
    gryffindor: dto.Team,
    slytherin: dto.Team,
):
    primary, secondary = await prepare_incompatible_players(dao, game, gryffindor, slytherin)

    resp = await client.post(
        "/admin/players/merge",
        json={
            "primary_id": primary.id,
            "secondary_id": secondary.id,
            "timeline": [
                {
                    "team_id": slytherin.id,
                    "date_joined": (GAME_START_AT - timedelta(days=30)).isoformat(),
                    "date_left": (GAME_START_AT + timedelta(days=3)).isoformat(),
                    "role": "мозг",
                    "emoji": "🐍",
                },
                {
                    "team_id": gryffindor.id,
                    "date_joined": (GAME_START_AT + timedelta(days=30)).isoformat(),
                    "permissions": {"can_manage_waivers": True},
                },
            ],
        },
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success, resp.text
    assert resp.json()["id"] == primary.id
    with pytest.raises(NoResultFound):
        await check_dao.player.get_by_id(secondary.id)
    history = await check_dao.team_player.get_history(primary)
    assert [tp.team_id for tp in history] == [slytherin.id, gryffindor.id]
    assert history[0].date_left == GAME_START_AT + timedelta(days=3)
    assert history[0].role == "мозг"
    assert history[0].emoji == "🐍"
    assert history[1].date_left is None
    assert history[1].role == DEFAULT_ROLE
    assert history[1].get_permissions()["can_manage_waivers"] is True
    assert history[1].get_permissions()["can_manage_players"] is False


@pytest.mark.asyncio
async def test_merge_players_naive_datetime_rejected(
    client: AsyncClient,
    admin_token: Token,
    dao: HolderDao,
    game: dto.FullGame,
    gryffindor: dto.Team,
    slytherin: dto.Team,
):
    primary, secondary = await prepare_incompatible_players(dao, game, gryffindor, slytherin)

    resp = await client.post(
        "/admin/players/merge",
        json={
            "primary_id": primary.id,
            "secondary_id": secondary.id,
            "timeline": [
                {
                    "team_id": slytherin.id,
                    # no timezone offset -> rejected
                    "date_joined": "2025-03-13T16:00:00",
                },
            ],
        },
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 422
    assert resp.json()["type"] == "MergeError"


@pytest.mark.asyncio
async def test_merge_players_timeline_violates_waiver_points(
    client: AsyncClient,
    admin_token: Token,
    dao: HolderDao,
    check_dao: HolderDao,
    game: dto.FullGame,
    gryffindor: dto.Team,
    slytherin: dto.Team,
):
    primary, secondary = await prepare_incompatible_players(dao, game, gryffindor, slytherin)

    # the timeline puts the player into gryffindor during the played game
    resp = await client.post(
        "/admin/players/merge",
        json={
            "primary_id": primary.id,
            "secondary_id": secondary.id,
            "timeline": [
                {
                    "team_id": gryffindor.id,
                    "date_joined": (GAME_START_AT - timedelta(days=30)).isoformat(),
                },
            ],
        },
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 422
    assert resp.json()["type"] == "MergeError"
    # nothing merged: the secondary player is still there
    assert (await check_dao.player.get_by_id(secondary.id)).id == secondary.id


@pytest.mark.asyncio
async def test_merge_players_overlapping_timeline_rejected(
    client: AsyncClient,
    admin_token: Token,
    dao: HolderDao,
    game: dto.FullGame,
    gryffindor: dto.Team,
    slytherin: dto.Team,
):
    primary, secondary = await prepare_incompatible_players(dao, game, gryffindor, slytherin)

    resp = await client.post(
        "/admin/players/merge",
        json={
            "primary_id": primary.id,
            "secondary_id": secondary.id,
            "timeline": [
                {
                    "team_id": slytherin.id,
                    "date_joined": (GAME_START_AT - timedelta(days=30)).isoformat(),
                },
                {
                    "team_id": gryffindor.id,
                    "date_joined": (GAME_START_AT + timedelta(days=30)).isoformat(),
                },
            ],
        },
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 422
    assert resp.json()["type"] == "MergeError"


@pytest.mark.asyncio
async def test_merge_teams(
    client: AsyncClient, admin_token: Token, dao: HolderDao, check_dao: HolderDao
):
    cap1 = await upsert_player(await upsert_user(create_dto_ron(), dao.user), dao.player)
    cap2 = await upsert_player(await upsert_user(create_dto_draco(), dao.user), dao.player)
    primary = await dao.team.create_no_chat("PrimaryTeam", None, cap1)
    secondary = await dao.team.create_no_chat("SecondaryTeam", None, cap2)
    await dao.commit()

    resp = await client.post(
        "/admin/teams/merge",
        json={"primary_id": primary.id, "secondary_id": secondary.id},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success, resp.text
    assert resp.json()["id"] == primary.id
    assert (await check_dao.team.get_by_id(primary.id)).id == primary.id
    with pytest.raises(NoResultFound):
        await check_dao.team.get_by_id(secondary.id)


@pytest.mark.asyncio
async def test_merge_forbidden_for_non_superuser(
    client: AsyncClient, hermione_token: Token, hermione: dto.Player
):
    resp = await client.post(
        "/admin/players/merge",
        json={"primary_id": hermione.id, "secondary_id": hermione.id},
        cookies=auth_cookies(hermione_token),
        follow_redirects=True,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_edit_completed_game_scenario(
    client: AsyncClient,
    admin_token: Token,
    game: dto.FullGame,
    author: dto.Player,
    dao: HolderDao,
    check_dao: HolderDao,
):
    await complete_game(game, dao)
    resp = await client.put(
        f"/admin/games/{game.id}/scenario",
        json={"scenario": ADMIN_SCENARIO},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success, resp.text
    body = resp.json()
    assert body["id"] == game.id
    assert body["name"] == ADMIN_SCENARIO["name"]
    assert len(body["levels"]) == len(ADMIN_SCENARIO["levels"])
    stored = await check_dao.game.get_full(game.id)
    assert stored.name == ADMIN_SCENARIO["name"]
    assert len(stored.levels) == len(ADMIN_SCENARIO["levels"])
    # the game stays completed; only its scenario changed
    assert stored.is_complete()
    # author is untouched when author_id is not supplied
    assert stored.author.id == author.id


@pytest.mark.asyncio
async def test_admin_change_completed_game_author(
    client: AsyncClient,
    admin_token: Token,
    harry: dto.Player,
    game: dto.FullGame,
    dao: HolderDao,
    check_dao: HolderDao,
):
    await complete_game(game, dao)
    resp = await client.put(
        f"/admin/games/{game.id}/scenario",
        json={"scenario": ADMIN_SCENARIO, "author_id": harry.id},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success, resp.text
    assert resp.json()["author"]["id"] == harry.id
    stored = await check_dao.game.get_by_id(game.id)
    assert stored.author.id == harry.id


@pytest.mark.asyncio
async def test_admin_edit_game_forbidden_for_non_superuser(
    client: AsyncClient,
    hermione_token: Token,
    game: dto.FullGame,
    dao: HolderDao,
):
    await complete_game(game, dao)
    resp = await client.put(
        f"/admin/games/{game.id}/scenario",
        json={"scenario": ADMIN_SCENARIO},
        cookies=auth_cookies(hermione_token),
        follow_redirects=True,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_upload_file_to_completed_game(
    client: AsyncClient,
    admin_token: Token,
    game: dto.FullGame,
    author: dto.Player,
    dao: HolderDao,
    check_dao: HolderDao,
):
    await complete_game(game, dao)
    resp = await client.post(
        f"/admin/games/{game.id}/files",
        files={"file": ("note.txt", b"admin uploaded", "text/plain")},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success, resp.text
    body = resp.json()
    assert body["guid"]
    assert body["original_filename"] == "note"
    assert body["extension"] == ".txt"
    stored = await check_dao.file_info.get_by_guid(body["guid"])
    # the uploaded file is owned by the game's author, not the acting admin
    assert stored.author_id == author.id


@pytest.mark.asyncio
async def test_admin_upload_file_forbidden_for_non_superuser(
    client: AsyncClient,
    hermione_token: Token,
    game: dto.FullGame,
    dao: HolderDao,
):
    await complete_game(game, dao)
    resp = await client.post(
        f"/admin/games/{game.id}/files",
        files={"file": ("note.txt", b"nope", "text/plain")},
        cookies=auth_cookies(hermione_token),
        follow_redirects=True,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_edit_non_completed_game_hidden(
    client: AsyncClient,
    admin_token: Token,
    game: dto.FullGame,
):
    # the game is under construction (not completed) — an admin must not reach it
    resp = await client.put(
        f"/admin/games/{game.id}/scenario",
        json={"scenario": ADMIN_SCENARIO},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 404, resp.text
    assert resp.json()["type"] == "GameNotFound"


@pytest.mark.asyncio
async def test_admin_upload_file_non_completed_game_hidden(
    client: AsyncClient,
    admin_token: Token,
    game: dto.FullGame,
):
    resp = await client.post(
        f"/admin/games/{game.id}/files",
        files={"file": ("note.txt", b"nope", "text/plain")},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 404, resp.text
    assert resp.json()["type"] == "GameNotFound"


@pytest.mark.asyncio
async def test_admin_cant_read_non_completed_game_scenario(
    client: AsyncClient,
    admin_token: Token,
    game: dto.FullGame,
):
    """Being a superuser grants no sight of a game still being written.

    The scenario of a game that is not complete belongs to its author and to
    the orgs the author gave ``view_scenario`` — admin rights are not a way in,
    not even knowing the game's id (the games list shows completed games only).
    """
    resp = await client.get(
        f"/games/{game.id}",
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["type"] == "NotAuthorizedForEdit"


@pytest.mark.asyncio
async def test_admin_cant_read_non_completed_game_as_own(
    client: AsyncClient,
    admin_token: Token,
    game: dto.FullGame,
):
    # the author-facing route is no way in either: the admin did not write it
    resp = await client.get(
        f"/games/my/{game.id}",
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["type"] == "NotAuthorizedForEdit"


@pytest.mark.asyncio
async def test_admin_cant_print_keys_of_non_completed_game(
    client: AsyncClient,
    admin_token: Token,
    game: dto.FullGame,
):
    # the keys sheet is the scenario's secret half — same rule as the card
    resp = await client.get(
        f"/games/my/{game.id}/keys/print",
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["type"] == "NotAuthorizedForEdit"


@pytest.mark.asyncio
async def test_admin_cant_read_file_of_non_completed_game(
    client: AsyncClient,
    admin_token: Token,
    game: dto.FullGame,
):
    # nor its media: a hint's picture is as much the scenario as its text
    resp = await client.get(
        f"/cdn/games/{game.id}/files/{GUID}",
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_admin_reads_the_scenario_once_the_game_is_complete(
    client: AsyncClient,
    admin_token: Token,
    game: dto.FullGame,
    dao: HolderDao,
):
    """The other side of the rule — and what makes the admin editor work.

    A complete game is public: the admin reads its scenario like everybody
    else, which is what the admin scenario editor loads before saving.
    """
    await complete_game(game, dao)
    resp = await client.get(
        f"/games/{game.id}",
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success, resp.text
    assert len(resp.json()["levels"]) == len(game.levels)


# ---------------------------------------------------------------------------
# Game statuses. An admin sees the games that stopped being drafts, and of them
# only the status — never the scenario, the keys or the files (that stays true
# for a running game: the tests below check it while the game is played).
# ---------------------------------------------------------------------------


async def set_status(game: dto.Game, status: GameStatus, dao: HolderDao) -> None:
    await dao.game.set_status(game, status)
    await dao.commit()


@pytest.mark.asyncio
async def test_admin_games_list_hides_drafts(
    client: AsyncClient,
    admin_token: Token,
    game: dto.FullGame,
):
    # the game is under construction — its author's alone
    resp = await client.get(
        "/admin/games",
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success, resp.text
    assert [g["id"] for g in resp.json()["content"]] == []


@pytest.mark.asyncio
async def test_admin_games_list_hides_ready_games(
    client: AsyncClient,
    admin_token: Token,
    game: dto.FullGame,
    dao: HolderDao,
):
    await set_status(game, GameStatus.ready, dao)
    resp = await client.get(
        "/admin/games",
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success, resp.text
    assert [g["id"] for g in resp.json()["content"]] == []


@pytest.mark.parametrize(
    "status",
    [GameStatus.getting_waivers, GameStatus.started, GameStatus.finished],
)
@pytest.mark.asyncio
async def test_admin_games_list_shows_active_games_without_content(
    client: AsyncClient,
    admin_token: Token,
    game: dto.FullGame,
    dao: HolderDao,
    status: GameStatus,
):
    await set_status(game, status, dao)
    resp = await client.get(
        "/admin/games",
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success, resp.text
    (listed,) = resp.json()["content"]
    assert listed["id"] == game.id
    assert listed["status"] == status.value
    # the status and the game's identity, nothing of what it is made of
    assert "levels" not in listed
    assert "scenario" not in listed


@pytest.mark.asyncio
async def test_admin_games_list_shows_completed_games(
    client: AsyncClient,
    admin_token: Token,
    game: dto.FullGame,
    dao: HolderDao,
):
    await set_status(game, GameStatus.finished, dao)
    await complete_game(game, dao)
    resp = await client.get(
        "/admin/games",
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success, resp.text
    (listed,) = resp.json()["content"]
    assert listed["id"] == game.id
    assert listed["status"] == GameStatus.complete.value
    assert "levels" not in listed


@pytest.mark.asyncio
async def test_admin_games_list_forbidden_for_non_superuser(
    client: AsyncClient,
    hermione_token: Token,
):
    resp = await client.get(
        "/admin/games",
        cookies=auth_cookies(hermione_token),
        follow_redirects=True,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_returns_game_from_waivers_to_under_construction(
    client: AsyncClient,
    admin_token: Token,
    game: dto.FullGame,
    dao: HolderDao,
    check_dao: HolderDao,
    scheduler: SchedulerMock,
):
    """The point of the whole feature — issue #164.

    Waivers were opened too early: the admin hands the game back to its author,
    and the start it was planned for goes with it, or the scheduler would start
    the game anyway a few minutes later.
    """
    await dao.game.set_start_at(game, GAME_START_AT)
    await set_status(game, GameStatus.getting_waivers, dao)
    resp = await client.put(
        f"/admin/games/{game.id}/status",
        json={"status": GameStatus.underconstruction.value},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success, resp.text
    assert resp.json()["status"] == GameStatus.underconstruction.value
    stored = await check_dao.game.get_by_id(game.id)
    assert stored.status == GameStatus.underconstruction
    assert stored.start_at is None
    assert scheduler.cancel_scheduled_game_calls


@pytest.mark.asyncio
async def test_admin_loses_the_game_once_it_is_a_draft_again(
    client: AsyncClient,
    admin_token: Token,
    game: dto.FullGame,
    dao: HolderDao,
):
    """After the save the game is the author's again — the admin cannot walk it
    back, and does not see it in the list any more."""
    await set_status(game, GameStatus.getting_waivers, dao)
    resp = await client.put(
        f"/admin/games/{game.id}/status",
        json={"status": GameStatus.underconstruction.value},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success, resp.text

    again = await client.put(
        f"/admin/games/{game.id}/status",
        json={"status": GameStatus.getting_waivers.value},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert again.status_code == 404, again.text
    assert again.json()["type"] == "GameNotFound"

    listed = await client.get(
        "/admin/games",
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert [g["id"] for g in listed.json()["content"]] == []


@pytest.mark.asyncio
async def test_admin_cant_change_status_of_a_draft(
    client: AsyncClient,
    admin_token: Token,
    game: dto.FullGame,
):
    resp = await client.put(
        f"/admin/games/{game.id}/status",
        json={"status": GameStatus.getting_waivers.value},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 404, resp.text
    assert resp.json()["type"] == "GameNotFound"


@pytest.mark.asyncio
async def test_admin_completes_a_finished_game(
    client: AsyncClient,
    admin_token: Token,
    game: dto.FullGame,
    dao: HolderDao,
    check_dao: HolderDao,
):
    await set_status(game, GameStatus.finished, dao)
    resp = await client.put(
        f"/admin/games/{game.id}/status",
        json={"status": GameStatus.complete.value},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success, resp.text
    stored = await check_dao.game.get_by_id(game.id)
    assert stored.is_complete()
    # completing is what gives a game its place in the archive
    assert stored.number is not None


@pytest.mark.asyncio
async def test_admin_cant_complete_a_game_that_is_not_finished(
    client: AsyncClient,
    admin_token: Token,
    game: dto.FullGame,
    dao: HolderDao,
):
    await set_status(game, GameStatus.started, dao)
    resp = await client.put(
        f"/admin/games/{game.id}/status",
        json={"status": GameStatus.complete.value},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["type"] == "GameNotFinished"


@pytest.mark.asyncio
async def test_admin_keeps_the_number_of_a_completed_game(
    client: AsyncClient,
    admin_token: Token,
    game: dto.FullGame,
    dao: HolderDao,
    check_dao: HolderDao,
):
    """A round trip out of `complete` and back must not renumber the archive."""
    await set_status(game, GameStatus.finished, dao)
    await complete_game(game, dao)
    number = (await check_dao.game.get_by_id(game.id)).number

    for status in (GameStatus.finished, GameStatus.complete):
        resp = await client.put(
            f"/admin/games/{game.id}/status",
            json={"status": status.value},
            cookies=auth_cookies(admin_token),
            follow_redirects=True,
        )
        assert resp.is_success, resp.text
    stored = await check_dao.game.get_by_id(game.id)
    assert stored.is_complete()
    assert stored.number == number


@pytest.mark.asyncio
async def test_admin_change_game_status_forbidden_for_non_superuser(
    client: AsyncClient,
    hermione_token: Token,
    game: dto.FullGame,
    dao: HolderDao,
):
    await set_status(game, GameStatus.getting_waivers, dao)
    resp = await client.put(
        f"/admin/games/{game.id}/status",
        json={"status": GameStatus.underconstruction.value},
        cookies=auth_cookies(hermione_token),
        follow_redirects=True,
    )
    assert resp.status_code == 403


@pytest.mark.parametrize(
    ("path", "status_code", "type_"),
    [
        ("/games/{id}", 403, "NotAuthorizedForEdit"),
        ("/games/my/{id}", 403, "NotAuthorizedForEdit"),
        ("/games/my/{id}/keys/print", 403, "NotAuthorizedForEdit"),
        ("/games/{id}/keys", 403, "NotAuthorizedForEdit"),
        # where every team stands right now, and the same table as a file
        ("/games/{id}/stat", 403, "NotAuthorizedForEdit"),
        ("/games/{id}/stat/export", 403, "NotAuthorizedForEdit"),
        # the media of a running game is offered by what the *team* has been
        # shown, so an admin in no team is turned away one step earlier
        (f"/cdn/games/{{id}}/files/{GUID}", 422, "PlayerNotInTeam"),
    ],
)
@pytest.mark.asyncio
async def test_admin_cant_read_content_of_a_running_game(
    client: AsyncClient,
    admin_token: Token,
    game: dto.FullGame,
    dao: HolderDao,
    path: str,
    status_code: int,
    type_: str,
):
    """A game being played is the one an admin must least be able to read.

    Seeing its status (and being able to change it) opens nothing else: the
    scenario, the key log, the results and the media all stay with the author
    and the orgs until the game is complete.
    """
    await set_status(game, GameStatus.started, dao)
    resp = await client.get(
        path.format(id=game.id),
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == status_code, resp.text
    assert resp.json()["type"] == type_


@pytest.mark.asyncio
async def test_admin_change_team_captain(
    client: AsyncClient,
    admin_token: Token,
    draco: dto.Player,
    hermione: dto.Player,
    slytherin: dto.Team,
    dao: HolderDao,
    check_dao: HolderDao,
):
    await dao.team_player.join_team(hermione, slytherin, role=DEFAULT_ROLE)
    await dao.commit()
    resp = await client.put(
        f"/admin/teams/{slytherin.id}/captain",
        json={"player_id": hermione.id},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success, resp.text
    resp.read()
    assert resp.json()["captain"]["id"] == hermione.id
    team = await check_dao.team.get_by_id(slytherin.id)
    assert team.captain is not None
    assert team.captain.id == hermione.id


@pytest.mark.asyncio
async def test_admin_change_team_captain_forbidden_for_non_superuser(
    client: AsyncClient,
    hermione_token: Token,
    hermione: dto.Player,
    draco: dto.Player,
    slytherin: dto.Team,
    dao: HolderDao,
    check_dao: HolderDao,
):
    await dao.team_player.join_team(hermione, slytherin, role=DEFAULT_ROLE)
    await dao.commit()
    resp = await client.put(
        f"/admin/teams/{slytherin.id}/captain",
        json={"player_id": hermione.id},
        cookies=auth_cookies(hermione_token),
        follow_redirects=True,
    )
    assert resp.status_code == 403
    team = await check_dao.team.get_by_id(slytherin.id)
    assert team.captain is not None
    assert team.captain.id == draco.id


@pytest.mark.asyncio
async def test_admin_add_player_to_team(
    client: AsyncClient,
    admin_token: Token,
    draco: dto.Player,
    hermione: dto.Player,
    slytherin: dto.Team,
    check_dao: HolderDao,
):
    # the admin is in neither team, so no team permission could authorise this
    resp = await client.post(
        f"/admin/teams/{slytherin.id}/players",
        json={"player_id": hermione.id, "role": "seeker", "emoji": "🐍"},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success, resp.text
    resp.read()
    body = resp.json()
    assert body["id"] == hermione.id
    assert body["role"] == "seeker"
    assert body["emoji"] == "🐍"
    team = await check_dao.team_player.get_team(hermione)
    assert team is not None
    assert team.id == slytherin.id


@pytest.mark.asyncio
async def test_admin_add_player_already_in_another_team(
    client: AsyncClient,
    admin_token: Token,
    draco: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    slytherin: dto.Team,
    dao: HolderDao,
    check_dao: HolderDao,
):
    await dao.team_player.join_team(hermione, gryffindor, role=DEFAULT_ROLE)
    await dao.commit()
    resp = await client.post(
        f"/admin/teams/{slytherin.id}/players",
        json={"player_id": hermione.id},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 422  # PlayerAlreadyInTeam -> SHError
    team = await check_dao.team_player.get_team(hermione)
    assert team is not None
    assert team.id == gryffindor.id


@pytest.mark.asyncio
async def test_admin_remove_player_from_team(
    client: AsyncClient,
    admin_token: Token,
    draco: dto.Player,
    hermione: dto.Player,
    slytherin: dto.Team,
    dao: HolderDao,
    check_dao: HolderDao,
):
    await dao.team_player.join_team(hermione, slytherin, role=DEFAULT_ROLE)
    await dao.commit()
    resp = await client.request(
        "DELETE",
        f"/admin/teams/{slytherin.id}/players/{hermione.id}",
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 204, resp.text
    assert await check_dao.team_player.get_team(hermione) is None


@pytest.mark.asyncio
async def test_admin_remove_player_forbidden_for_non_superuser(
    client: AsyncClient,
    hermione_token: Token,
    draco: dto.Player,
    hermione: dto.Player,
    slytherin: dto.Team,
    dao: HolderDao,
    check_dao: HolderDao,
):
    await dao.team_player.join_team(hermione, slytherin, role=DEFAULT_ROLE)
    await dao.commit()
    resp = await client.request(
        "DELETE",
        f"/admin/teams/{slytherin.id}/players/{draco.id}",
        cookies=auth_cookies(hermione_token),
        follow_redirects=True,
    )
    assert resp.status_code == 403
    assert await check_dao.team_player.get_team(draco) is not None


# ---------------------------------------------------------------------------
# Resending the running level's messages (issue shvatka-ui#185). The one thing
# the panel may do to a game being played — and it does it blind: the answer
# names the teams the request covered and nothing about where any of them is.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_resends_the_running_level_to_one_team(
    client: AsyncClient,
    admin_token: Token,
    started_game: dto.FullGame,
    gryffindor: dto.Team,
):
    resp = await client.post(
        "/admin/games/running/resend",
        json={"team_id": gryffindor.id},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 200, resp.text
    assert [team["id"] for team in resp.json()["items"]] == [gryffindor.id]
    # the answer carries the team, never a level, a hint or a position in the game
    assert "level" not in resp.text
    assert "hint" not in resp.text


@pytest.mark.asyncio
async def test_admin_resends_the_running_level_to_every_team(
    client: AsyncClient,
    admin_token: Token,
    started_game: dto.FullGame,
    gryffindor: dto.Team,
    slytherin: dto.Team,
):
    resp = await client.post(
        "/admin/games/running/resend",
        json={},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 200, resp.text
    assert {team["id"] for team in resp.json()["items"]} == {gryffindor.id, slytherin.id}


@pytest.mark.asyncio
async def test_admin_cant_resend_to_a_team_that_does_not_play(
    client: AsyncClient,
    admin_token: Token,
    started_game: dto.FullGame,
    gryffindor: dto.Team,
):
    """Naming a team that is not in the game answers the same either way.

    A refusal that told a stranger's id from a player's would be a way to read
    the game's roster out of the panel one guess at a time.
    """
    resp = await client.post(
        "/admin/games/running/resend",
        json={"team_id": gryffindor.id + 1000},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["type"] == "TeamError"


@pytest.mark.asyncio
async def test_admin_cant_resend_before_the_game_runs(
    client: AsyncClient,
    admin_token: Token,
    game: dto.FullGame,
    dao: HolderDao,
):
    await set_status(game, GameStatus.getting_waivers, dao)
    resp = await client.post(
        "/admin/games/running/resend",
        json={},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["type"] == "GameStatusError"


@pytest.mark.asyncio
async def test_admin_resend_forbidden_for_non_superuser(
    client: AsyncClient,
    hermione_token: Token,
    started_game: dto.FullGame,
    gryffindor: dto.Team,
):
    resp = await client.post(
        "/admin/games/running/resend",
        json={"team_id": gryffindor.id},
        cookies=auth_cookies(hermione_token),
        follow_redirects=True,
    )
    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# Purging a false start. Rewinding a played game leaves its run behind, and the
# game replayed on the right evening would start with every team already on the
# level it reached — so the move may take the run with it.
# ---------------------------------------------------------------------------


async def count_runtime(dao: HolderDao) -> tuple[int, int, int, int]:
    """The four tables a game's run writes into."""
    return (
        await dao.level_time.count(),
        await dao.key_time.count(),
        await dao.events.count(),
        await dao.timers.count(),
    )


@pytest.mark.asyncio
async def test_admin_purges_the_run_when_rewinding_a_played_game(
    client: AsyncClient,
    admin_token: Token,
    finished_game: dto.FullGame,
    check_dao: HolderDao,
):
    level_times, keys, events, _ = await count_runtime(check_dao)
    assert level_times > 0
    assert keys > 0
    assert events > 0

    resp = await client.put(
        f"/admin/games/{finished_game.id}/status",
        json={"status": GameStatus.getting_waivers.value, "purge_runtime": True},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success, resp.text
    assert resp.json()["status"] == GameStatus.getting_waivers.value
    assert await count_runtime(check_dao) == (0, 0, 0, 0)
    stored = await check_dao.game.get_by_id(finished_game.id)
    assert stored.status == GameStatus.getting_waivers


@pytest.mark.asyncio
async def test_the_purge_keeps_the_waivers(
    client: AsyncClient,
    admin_token: Token,
    finished_game: dto.FullGame,
    check_dao: HolderDao,
):
    """Who signed up survives a false start — that is the point of rewinding to
    ``getting_waivers`` rather than to a draft."""
    before = await check_dao.waiver.get_all_by_game(finished_game)
    assert before

    resp = await client.put(
        f"/admin/games/{finished_game.id}/status",
        json={"status": GameStatus.getting_waivers.value, "purge_runtime": True},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success, resp.text
    after = await check_dao.waiver.get_all_by_game(finished_game)
    assert {(w.player.id, w.team.id, w.played) for w in after} == {
        (w.player.id, w.team.id, w.played) for w in before
    }


@pytest.mark.asyncio
async def test_a_status_change_without_the_box_keeps_the_run(
    client: AsyncClient,
    admin_token: Token,
    finished_game: dto.FullGame,
    check_dao: HolderDao,
):
    before = await count_runtime(check_dao)
    resp = await client.put(
        f"/admin/games/{finished_game.id}/status",
        json={"status": GameStatus.getting_waivers.value},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success, resp.text
    assert await count_runtime(check_dao) == before


@pytest.mark.asyncio
async def test_the_purge_is_refused_on_a_move_that_is_not_a_rewind(
    client: AsyncClient,
    admin_token: Token,
    finished_game: dto.FullGame,
    check_dao: HolderDao,
):
    """Completing a game is not undoing it — the run is its history."""
    before = await count_runtime(check_dao)
    resp = await client.put(
        f"/admin/games/{finished_game.id}/status",
        json={"status": GameStatus.complete.value, "purge_runtime": True},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["type"] == "GameStatusError"
    assert await count_runtime(check_dao) == before
    stored = await check_dao.game.get_by_id(finished_game.id)
    assert stored.status == GameStatus.finished


@pytest.mark.asyncio
async def test_purge_forbidden_for_non_superuser(
    client: AsyncClient,
    hermione_token: Token,
    finished_game: dto.FullGame,
    check_dao: HolderDao,
):
    before = await count_runtime(check_dao)
    resp = await client.put(
        f"/admin/games/{finished_game.id}/status",
        json={"status": GameStatus.getting_waivers.value, "purge_runtime": True},
        cookies=auth_cookies(hermione_token),
        follow_redirects=True,
    )
    assert resp.status_code == 403, resp.text
    assert await count_runtime(check_dao) == before


# ---------------------------------------------------------------------------
# Editing a game's roster from the panel: the way in when the captain is gone,
# missed the deadline, or simply left somebody out.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_adds_a_waiver(
    client: AsyncClient,
    admin_token: Token,
    game_with_waivers: dto.FullGame,
    gryffindor: dto.Team,
    ron: dto.Player,
    check_dao: HolderDao,
):
    # ron voted `no` and is not in the roster
    assert ron.id not in {
        p.player.id for p in await check_dao.waiver.get_played(game_with_waivers, gryffindor)
    }

    resp = await client.post(
        f"/admin/waivers/game/{game_with_waivers.id}/teams/{gryffindor.id}/players",
        json={"player_id": ron.id},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success, resp.text
    body = resp.json()
    assert body["team"]["id"] == gryffindor.id
    assert body["players"]
    stored = await check_dao.waiver.get_player_waiver(game_with_waivers, ron, gryffindor)
    assert stored is not None
    assert stored.played == Played.yes


@pytest.mark.asyncio
async def test_admin_removes_a_waiver(
    client: AsyncClient,
    admin_token: Token,
    game_with_waivers: dto.FullGame,
    gryffindor: dto.Team,
    harry: dto.Player,
    check_dao: HolderDao,
):
    assert await check_dao.waiver.get_player_waiver(game_with_waivers, harry, gryffindor)

    resp = await client.request(
        "DELETE",
        f"/admin/waivers/game/{game_with_waivers.id}" f"/teams/{gryffindor.id}/players/{harry.id}",
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 204, resp.text
    # the row goes rather than becoming `revoked` — the team may sign the
    # player up again afterwards
    assert await check_dao.waiver.get_player_waiver(game_with_waivers, harry, gryffindor) is None


@pytest.mark.asyncio
async def test_admin_cant_sign_up_a_player_of_another_team(
    client: AsyncClient,
    admin_token: Token,
    game_with_waivers: dto.FullGame,
    gryffindor: dto.Team,
    draco: dto.Player,
    check_dao: HolderDao,
):
    resp = await client.post(
        f"/admin/waivers/game/{game_with_waivers.id}/teams/{gryffindor.id}/players",
        json={"player_id": draco.id},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["type"] == "PlayerNotInTeam"
    assert await check_dao.waiver.get_player_waiver(game_with_waivers, draco, gryffindor) is None


@pytest.mark.asyncio
async def test_admin_waiver_edit_forbidden_for_non_superuser(
    client: AsyncClient,
    hermione_token: Token,
    game_with_waivers: dto.FullGame,
    gryffindor: dto.Team,
    harry: dto.Player,
    ron: dto.Player,
    check_dao: HolderDao,
):
    added = await client.post(
        f"/admin/waivers/game/{game_with_waivers.id}/teams/{gryffindor.id}/players",
        json={"player_id": ron.id},
        cookies=auth_cookies(hermione_token),
        follow_redirects=True,
    )
    assert added.status_code == 403, added.text

    removed = await client.request(
        "DELETE",
        f"/admin/waivers/game/{game_with_waivers.id}" f"/teams/{gryffindor.id}/players/{harry.id}",
        cookies=auth_cookies(hermione_token),
        follow_redirects=True,
    )
    assert removed.status_code == 403, removed.text
    assert await check_dao.waiver.get_player_waiver(game_with_waivers, harry, gryffindor)
