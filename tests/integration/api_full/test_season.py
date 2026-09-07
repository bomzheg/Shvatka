from datetime import date, datetime, timedelta

import pytest
from dishka import AsyncContainer
from httpx import AsyncClient

from shvatka.api.app.dependencies.auth import AuthProperties
from shvatka.api.auth.responses import Token
from shvatka.core.models import dto
from shvatka.core.season.interactors import PublishSeasonDigestInteractor
from shvatka.core.utils.datetime_utils import tz_game, tz_utc
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.mocks.season import MOCK_MESSAGE_ID, SeasonAnnouncerMock

YEAR = 2077
FIRST = date(YEAR, 5, 15)
SECOND = date(YEAR, 6, 5)


def auth_cookies(token: Token) -> dict[str, str]:
    return {"Authorization": f"{token.token_type} {token.access_token}"}


@pytest.fixture
def harry_token(harry: dto.Player, auth: AuthProperties) -> Token:
    return auth.create_user_token(harry)


@pytest.fixture
def hermione_token(hermione: dto.Player, auth: AuthProperties) -> Token:
    return auth.create_user_token(hermione)


@pytest.fixture
def draco_token(draco: dto.Player, auth: AuthProperties) -> Token:
    return auth.create_user_token(draco)


@pytest.fixture
def author_token(author: dto.Player, auth: AuthProperties) -> Token:
    return auth.create_user_token(author)


async def publish(client: AsyncClient, token: Token, year: int = YEAR, slots=None):
    slots = slots or [
        {"date": FIRST.isoformat()},
        {"date": SECOND.isoformat(), "note": "зимняя игра"},
    ]
    return await client.post(
        "/seasons",
        cookies=auth_cookies(token),
        json={"year": year, "slots": slots},
        follow_redirects=True,
    )


async def take(client: AsyncClient, token: Token, slot_id: int, **body):
    return await client.post(
        f"/seasons/{YEAR}/slots/{slot_id}/take",
        cookies=auth_cookies(token),
        json={"author_kind": "player", **body},
        follow_redirects=True,
    )


async def feed_of(client: AsyncClient, token: Token) -> list[dict]:
    resp = await client.get("/notifications", cookies=auth_cookies(token), follow_redirects=True)
    assert resp.is_success
    resp.read()
    return resp.json()["items"]


@pytest.mark.asyncio
async def test_default_dates_are_nine_saturdays(client: AsyncClient):
    resp = await client.get("/seasons/defaults", params={"year": 2027}, follow_redirects=True)

    assert resp.is_success
    body = resp.json()
    assert body["year"] == 2027
    assert len(body["dates"]) == 9
    assert body["dates"][0] == "2027-05-15"


@pytest.mark.asyncio
async def test_publish_writes_announces_and_notifies(
    client: AsyncClient,
    harry: dto.Player,
    harry_token: Token,
    gryffindor: dto.Team,
    check_dao: HolderDao,
    dishka: AsyncContainer,
):
    announcer = await dishka.get(SeasonAnnouncerMock)
    announcer.clear()

    resp = await publish(client, harry_token)

    assert resp.is_success
    body = resp.json()
    assert body["year"] == YEAR
    assert [slot["date"] for slot in body["slots"]] == [FIRST.isoformat(), SECOND.isoformat()]

    season = await check_dao.season.get_season(YEAR)
    assert season is not None
    assert season.log_message_id == MOCK_MESSAGE_ID
    assert [slot.date for slot in season.slots] == [FIRST, SECOND]
    assert [one.year for one in announcer.published] == [YEAR]

    # everyone who has been in a team recently hears about it
    feed = await feed_of(client, harry_token)
    assert [one["type"] for one in feed] == ["season_schedule_changed"]
    assert feed[0]["payload"]["year"] == YEAR
    assert feed[0]["severity"] == "low"

    # publication itself is not a change: the first digest describes changes to it
    assert await check_dao.season_change.get_unpublished_changes(season.id) == []


@pytest.mark.asyncio
async def test_publishing_the_same_year_twice_is_a_conflict(
    client: AsyncClient, harry: dto.Player, harry_token: Token
):
    assert (await publish(client, harry_token)).is_success

    resp = await publish(client, harry_token)

    assert resp.status_code == 409
    assert resp.json()["type"] == "SeasonAlreadyExists"


@pytest.mark.asyncio
async def test_a_date_outside_the_season_year_is_refused(
    client: AsyncClient, harry: dto.Player, harry_token: Token
):
    resp = await publish(client, harry_token, slots=[{"date": f"{YEAR + 1}-05-15"}])

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_reading_a_season_needs_no_authentication(
    client: AsyncClient, harry: dto.Player, harry_token: Token
):
    assert (await publish(client, harry_token)).is_success

    resp = await client.get(f"/seasons/{YEAR}", follow_redirects=True)

    assert resp.is_success
    assert resp.json()["year"] == YEAR
    years = await client.get("/seasons", follow_redirects=True)
    assert years.json()["years"] == [YEAR]


@pytest.mark.asyncio
async def test_taking_a_date_locks_it_to_its_owner(
    client: AsyncClient,
    harry: dto.Player,
    harry_token: Token,
    draco: dto.Player,
    draco_token: Token,
    check_dao: HolderDao,
):
    published = await publish(client, harry_token)
    slot_id = published.json()["slots"][0]["id"]

    taken = await take(client, harry_token, slot_id, org_player_ids=[draco.id])
    assert taken.is_success
    assert taken.json()["owner"]["id"] == harry.id
    assert [org["id"] for org in taken.json()["orgs"]] == [draco.id]

    # a second taker is a conflict, not a silent overwrite
    second = await take(client, draco_token, slot_id)
    assert second.status_code == 409
    assert second.json()["type"] == "SlotAlreadyTaken"

    slot = await check_dao.season_slot.get_slot(slot_id)
    assert slot.owner is not None
    assert slot.owner.id == harry.id

    # and the change is recorded, for the daily digest to collapse
    season = await check_dao.season.get_season(YEAR)
    assert season is not None
    changes = await check_dao.season_change.get_unpublished_changes(season.id)
    assert [change.type.name for change in changes] == ["slot_taken"]


@pytest.mark.asyncio
async def test_a_player_without_promotion_may_not_take_a_date(
    client: AsyncClient,
    harry: dto.Player,
    harry_token: Token,
    hermione: dto.Player,
    hermione_token: Token,
):
    published = await publish(client, harry_token)
    slot_id = published.json()["slots"][0]["id"]

    resp = await take(client, hermione_token, slot_id)

    assert resp.status_code == 403
    assert resp.json()["type"] == "CantBeAuthor"


@pytest.mark.asyncio
async def test_someone_elses_date_may_not_be_moved(
    client: AsyncClient,
    harry: dto.Player,
    harry_token: Token,
    draco: dto.Player,
    draco_token: Token,
):
    published = await publish(client, harry_token)
    slot_id = published.json()["slots"][0]["id"]
    assert (await take(client, harry_token, slot_id)).is_success

    resp = await client.patch(
        f"/seasons/{YEAR}/slots/{slot_id}",
        cookies=auth_cookies(draco_token),
        json={"date": (FIRST + timedelta(days=1)).isoformat()},
        follow_redirects=True,
    )

    assert resp.status_code == 403
    assert resp.json()["type"] == "NotSlotOwner"


@pytest.mark.asyncio
async def test_linking_a_game_takes_the_date_and_syncs_it(
    client: AsyncClient,
    author: dto.Player,
    author_token: Token,
    game: dto.FullGame,
    dao: HolderDao,
    check_dao: HolderDao,
):
    start_at = datetime(YEAR, 5, 17, 20, tzinfo=tz_game)
    await dao.game.set_start_at(game, start_at)
    await dao.commit()
    published = await publish(client, author_token)
    slots = published.json()["slots"]

    resp = await client.post(
        f"/seasons/{YEAR}/slots/{slots[0]['id']}/game",
        cookies=auth_cookies(author_token),
        json={"game_id": game.id},
        follow_redirects=True,
    )

    assert resp.is_success
    slot = await check_dao.season_slot.get_slot(slots[0]["id"])
    assert slot.game is not None
    assert slot.game.id == game.id
    # the date follows the game, and taking it happens on the way
    assert slot.date == start_at.date()
    assert slot.owner is not None
    assert slot.owner.id == game.author.id

    # the same game cannot sit in two dates
    second = await client.post(
        f"/seasons/{YEAR}/slots/{slots[1]['id']}/game",
        cookies=auth_cookies(author_token),
        json={"game_id": game.id},
        follow_redirects=True,
    )
    assert second.status_code == 409
    assert second.json()["type"] == "GameAlreadyInSchedule"


@pytest.mark.asyncio
async def test_replanning_the_game_drags_its_date_along(
    client: AsyncClient,
    author: dto.Player,
    author_token: Token,
    game: dto.FullGame,
    dao: HolderDao,
    check_dao: HolderDao,
):
    await dao.game.set_start_at(game, datetime(YEAR, 5, 15, 20, tzinfo=tz_game))
    await dao.commit()
    published = await publish(client, author_token)
    slot_id = published.json()["slots"][0]["id"]
    assert (
        await client.post(
            f"/seasons/{YEAR}/slots/{slot_id}/game",
            cookies=auth_cookies(author_token),
            json={"game_id": game.id},
            follow_redirects=True,
        )
    ).is_success

    moved_to = datetime(YEAR, 5, 22, 20, tzinfo=tz_game)
    replanned = await client.put(
        f"/games/my/{game.id}/start_at",
        cookies=auth_cookies(author_token),
        json={"start_at": moved_to.isoformat()},
        follow_redirects=True,
    )

    assert replanned.is_success
    slot = await check_dao.season_slot.get_slot(slot_id)
    assert slot.date == moved_to.date()


@pytest.mark.asyncio
async def test_suggested_dates_are_the_nearby_free_ones(
    client: AsyncClient, harry: dto.Player, harry_token: Token
):
    assert (await publish(client, harry_token)).is_success

    resp = await client.get(
        "/seasons/slots/suggest",
        params={"at": datetime(YEAR, 5, 16, 20, tzinfo=tz_game).isoformat()},
        cookies=auth_cookies(harry_token),
        follow_redirects=True,
    )

    assert resp.is_success
    assert [slot["date"] for slot in resp.json()] == [FIRST.isoformat()]


@pytest.mark.asyncio
async def test_the_digest_collapses_marks_and_notifies(
    client: AsyncClient,
    harry: dto.Player,
    harry_token: Token,
    gryffindor: dto.Team,
    check_dao: HolderDao,
    dishka_request: AsyncContainer,
    dishka: AsyncContainer,
):
    published = await publish(client, harry_token)
    slot_id = published.json()["slots"][0]["id"]
    for day in (FIRST + timedelta(days=1), FIRST + timedelta(days=2)):
        moved = await client.patch(
            f"/seasons/{YEAR}/slots/{slot_id}",
            cookies=auth_cookies(harry_token),
            json={"date": day.isoformat()},
            follow_redirects=True,
        )
        assert moved.is_success
    announcer = await dishka.get(SeasonAnnouncerMock)
    announcer.clear()

    interactor = await dishka_request.get(PublishSeasonDigestInteractor)
    await interactor(now=datetime.now(tz=tz_utc))

    season = await check_dao.season.get_season(YEAR)
    assert season is not None
    assert await check_dao.season_change.get_unpublished_changes(season.id) == []
    # two moves of one date collapse into one line
    assert len(announcer.digests) == 1
    _, digests = announcer.digests[0]
    assert len(digests) == 1
    assert digests[0].date_before == FIRST
    assert digests[0].date_after == FIRST + timedelta(days=2)

    changed = [one for one in await feed_of(client, harry_token) if "changes" in one["payload"]]
    assert [one["payload"]["changes"] for one in changed] == [1]


@pytest.mark.asyncio
async def test_a_finished_season_is_unpinned_once(
    client: AsyncClient,
    harry: dto.Player,
    harry_token: Token,
    check_dao: HolderDao,
    dishka_request: AsyncContainer,
    dishka: AsyncContainer,
):
    past = 2020
    published = await publish(client, harry_token, year=past, slots=[{"date": f"{past}-05-16"}])
    assert published.is_success
    announcer = await dishka.get(SeasonAnnouncerMock)
    announcer.clear()

    interactor = await dishka_request.get(PublishSeasonDigestInteractor)
    await interactor(now=datetime.now(tz=tz_utc))

    season = await check_dao.season.get_season(past)
    assert season is not None
    assert season.unpinned_at is not None
    assert [one.year for one in announcer.closed] == [past]

    # the second run has nothing left to close
    announcer.clear()
    await interactor(now=datetime.now(tz=tz_utc))
    assert announcer.closed == []
