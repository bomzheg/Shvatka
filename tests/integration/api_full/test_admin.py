from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.exc import NoResultFound

from shvatka.api.dependencies.auth import AuthProperties
from shvatka.api.models.auth import Token
from shvatka.core.models import dto
from shvatka.core.models.enums.played import Played
from shvatka.core.players.player import upsert_player
from shvatka.core.services.user import upsert_user
from shvatka.core.utils.defaults_constants import DEFAULT_ROLE
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.user_constants import (
    create_dto_hermione,
    create_dto_ron,
    create_dto_draco,
)

GAME_START_AT = datetime(2025, 4, 12, 16, 0, tzinfo=timezone.utc)

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
    assert datetime.fromisoformat(point["at_since"]) == GAME_START_AT - timedelta(hours=12)
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
