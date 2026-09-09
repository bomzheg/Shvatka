from datetime import date, datetime, timedelta

import pytest

from shvatka.core.models import dto
from shvatka.core.models.dto import GameResults
from shvatka.core.models.enums import GameStatus
from shvatka.core.models.enums.notification import NotificationSeverity, NotificationType
from shvatka.core.season import dto as season_dto
from shvatka.core.season.interactors import (
    AddSlotInteractor,
    EditSlotNoteInteractor,
    FindSlotsNearGameStartInteractor,
    GetCurrentSeasonInteractor,
    GetDefaultSlotDatesInteractor,
    GetSeasonInteractor,
    LinkGameToSlotInteractor,
    ListSeasonsInteractor,
    MoveSlotInteractor,
    PublishSeasonDigestInteractor,
    PublishSeasonInteractor,
    ReleaseSlotInteractor,
    RemoveSlotInteractor,
    SetSlotOrgsInteractor,
    SyncLinkedSlotInteractor,
    TakeSlotInteractor,
    UnlinkGameFromSlotInteractor,
)
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_game
from tests.fixtures.identity import MockIdentityProvider
from tests.mocks.season import MOCK_CHAT_ID, MOCK_MESSAGE_ID, SeasonAnnouncerMock
from tests.unit.season.conftest import make_player, make_team
from tests.unit.season.fake_dao import NOW, FakeSeasonDao

YEAR = 2027
FIRST = date(YEAR, 5, 15)
SECOND = date(YEAR, 6, 5)

AUTHOR = make_player(1)
OTHER = make_player(2)
PLAIN = make_player(3, can_be_author=False)
TEAM = make_team(10, AUTHOR)
GAME = dto.Game(
    id=7,
    author=AUTHOR,
    name="Пони",
    status=GameStatus.ready,
    manage_token="token",
    start_at=datetime(YEAR, 5, 17, 20, tzinfo=tz_game),
    number=None,
    results=GameResults(published_chanel_id=None, results_picture_file_id=None, keys_url=None),
)


def make_dao(**kwargs) -> FakeSeasonDao:
    return FakeSeasonDao(
        players=[AUTHOR, OTHER, PLAIN],
        teams=[TEAM],
        games=[GAME],
        recipients={1, 2, 3},
        **kwargs,
    )


def identity(player: dto.Player = AUTHOR, *, superuser: bool = False) -> MockIdentityProvider:
    return MockIdentityProvider(player=player, superuser=player if superuser else None)


async def publish(dao: FakeSeasonDao, announcer: SeasonAnnouncerMock, dates=(FIRST, SECOND)):
    await PublishSeasonInteractor(dao=dao, announcer=announcer)(
        YEAR,
        [season_dto.SlotDraft(date=day) for day in dates],
        identity=identity(),
    )
    announcer.clear()
    dao.notifications.clear()
    return await dao.get_season(YEAR)


# ---------- reading ----------


@pytest.mark.asyncio
async def test_default_dates_persist_nothing():
    dao = make_dao()

    dates = await GetDefaultSlotDatesInteractor()(YEAR)

    assert dates[0] == FIRST
    assert dao.seasons == {}
    assert dao.commits == 0


@pytest.mark.asyncio
async def test_an_unpublished_year_is_not_found():
    with pytest.raises(exceptions.SeasonNotFound):
        await GetSeasonInteractor(dao=make_dao(), announcer=SeasonAnnouncerMock())(YEAR)


@pytest.mark.asyncio
async def test_the_current_season_is_the_one_of_today_in_msk():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    await publish(dao, announcer)

    season = await GetCurrentSeasonInteractor(dao=dao, announcer=announcer)(
        datetime(YEAR, 12, 31, 23, tzinfo=tz_game)
    )

    assert season.year == YEAR


@pytest.mark.asyncio
async def test_the_years_are_listed_newest_first():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    await publish(dao, announcer)
    await PublishSeasonInteractor(dao=dao, announcer=announcer)(
        YEAR + 1, [season_dto.SlotDraft(date=date(YEAR + 1, 5, 13))], identity=identity()
    )

    assert list(await ListSeasonsInteractor(dao=dao)()) == [YEAR + 1, YEAR]


# ---------- publishing ----------


@pytest.mark.asyncio
async def test_publishing_stores_announces_and_notifies():
    dao, announcer = make_dao(), SeasonAnnouncerMock()

    season = await PublishSeasonInteractor(dao=dao, announcer=announcer)(
        YEAR,
        [season_dto.SlotDraft(date=SECOND), season_dto.SlotDraft(date=FIRST, note="город")],
        identity=identity(),
    )

    assert [slot.date for slot in season.slots] == [FIRST, SECOND]
    assert season.log_chat_id == MOCK_CHAT_ID
    assert season.log_message_id == MOCK_MESSAGE_ID
    assert [one.year for one in announcer.published] == [YEAR]
    # publication is not a change: the first digest describes changes *to* it
    assert dao.changes == []
    sent = dao.notifications[0]
    assert sent.type == NotificationType.season_schedule_changed
    assert sent.severity == NotificationSeverity.low
    assert sent.payload == {"year": YEAR, "published": True, "slots": 2}
    assert sent.recipient_ids == {1, 2, 3}


@pytest.mark.asyncio
async def test_the_audience_reaches_back_to_last_january():
    dao, announcer = make_dao(), SeasonAnnouncerMock()

    await publish(dao, announcer)

    assert dao.audience_since == datetime(NOW.year - 1, 1, 1, tzinfo=tz_game)


@pytest.mark.asyncio
async def test_a_channel_that_refuses_the_post_does_not_lose_the_season():
    class Refusing(SeasonAnnouncerMock):
        async def publish(self, season):
            raise RuntimeError("telegram said no")

    dao, announcer = make_dao(), Refusing()

    season = await PublishSeasonInteractor(dao=dao, announcer=announcer)(
        YEAR, [season_dto.SlotDraft(date=FIRST)], identity=identity()
    )

    assert season.log_message_id is None
    assert len(season.slots) == 1
    assert dao.notifications


@pytest.mark.asyncio
async def test_the_same_year_cannot_be_published_twice():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    await publish(dao, announcer)

    with pytest.raises(exceptions.SeasonAlreadyExists):
        await publish(dao, announcer)


@pytest.mark.asyncio
async def test_a_season_needs_at_least_one_date():
    with pytest.raises(exceptions.SeasonError):
        await PublishSeasonInteractor(dao=make_dao(), announcer=SeasonAnnouncerMock())(
            YEAR, [], identity=identity()
        )


@pytest.mark.asyncio
async def test_a_date_outside_the_year_is_refused():
    with pytest.raises(exceptions.SeasonError):
        await PublishSeasonInteractor(dao=make_dao(), announcer=SeasonAnnouncerMock())(
            YEAR, [season_dto.SlotDraft(date=date(YEAR + 1, 5, 15))], identity=identity()
        )


@pytest.mark.asyncio
async def test_only_an_author_publishes():
    with pytest.raises(exceptions.CantBeAuthor):
        await PublishSeasonInteractor(dao=make_dao(), announcer=SeasonAnnouncerMock())(
            YEAR, [season_dto.SlotDraft(date=FIRST)], identity=identity(PLAIN)
        )


# ---------- editing one date ----------


@pytest.mark.asyncio
async def test_adding_a_date_records_it_and_refreshes_the_message():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    await publish(dao, announcer)

    slot = await AddSlotInteractor(dao=dao, announcer=announcer)(
        YEAR, date(YEAR, 7, 3), "зимняя игра", identity=identity()
    )

    assert slot.note == "зимняя игра"
    assert [change.type for change in dao.changes] == [season_dto.ChangeType.slot_added]
    assert len(announcer.updated) == 1


@pytest.mark.asyncio
async def test_moving_a_date_records_where_it_came_from():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    season = await publish(dao, announcer)
    slot_id = season.slots[0].id

    moved = await MoveSlotInteractor(dao=dao, announcer=announcer)(
        YEAR, slot_id, date(YEAR, 5, 22), identity=identity()
    )

    assert moved.date == date(YEAR, 5, 22)
    assert dao.changes[0].payload["from"] == FIRST.isoformat()
    assert dao.changes[0].payload["to"] == date(YEAR, 5, 22).isoformat()


@pytest.mark.asyncio
async def test_moving_a_date_onto_itself_changes_nothing():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    season = await publish(dao, announcer)

    await MoveSlotInteractor(dao=dao, announcer=announcer)(
        YEAR, season.slots[0].id, FIRST, identity=identity()
    )

    assert dao.changes == []
    assert announcer.updated == []


@pytest.mark.asyncio
async def test_a_note_is_recorded_and_can_be_cleared():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    season = await publish(dao, announcer)
    editor = EditSlotNoteInteractor(dao=dao, announcer=announcer)

    await editor(YEAR, season.slots[0].id, "город", identity=identity())
    cleared = await editor(YEAR, season.slots[0].id, None, identity=identity())

    assert cleared.note is None
    assert [change.payload["note"] for change in dao.changes] == ["город", None]


@pytest.mark.asyncio
async def test_removing_a_date_keeps_the_change_that_describes_it():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    season = await publish(dao, announcer)
    slot_id, survivor_id = season.slots[0].id, season.slots[1].id

    await RemoveSlotInteractor(dao=dao, announcer=announcer)(YEAR, slot_id, identity=identity())

    assert [slot.id for slot in dao.slots] == [survivor_id]
    assert dao.changes[0].type == season_dto.ChangeType.slot_removed
    # the date is gone, so the fk nulls the link — the payload is all that is left
    assert dao.changes[0].slot_id is None
    assert dao.changes[0].payload["date"] == FIRST.isoformat()


@pytest.mark.asyncio
async def test_an_unknown_date_is_not_found():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    await publish(dao, announcer)

    with pytest.raises(exceptions.SlotNotFound):
        await MoveSlotInteractor(dao=dao, announcer=announcer)(
            YEAR, 9999, SECOND, identity=identity()
        )


# ---------- ownership ----------


@pytest.mark.asyncio
async def test_taking_a_date_locks_it_and_names_its_orgs():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    season = await publish(dao, announcer)
    slot_id = season.slots[0].id

    slot = await TakeSlotInteractor(dao=dao, announcer=announcer)(
        YEAR,
        slot_id,
        author_kind=season_dto.SlotAuthorKind.player,
        team_id=None,
        org_player_ids=[OTHER.id, OTHER.id],
        identity=identity(),
    )

    assert slot.owner == AUTHOR
    assert [org.id for org in slot.orgs] == [OTHER.id]
    assert dao.locked == [slot_id]
    assert dao.changes[0].payload["author"] == AUTHOR.name_mention


@pytest.mark.asyncio
async def test_a_team_date_records_the_team_as_the_author():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    season = await publish(dao, announcer)

    slot = await TakeSlotInteractor(dao=dao, announcer=announcer)(
        YEAR,
        season.slots[0].id,
        author_kind=season_dto.SlotAuthorKind.team,
        team_id=TEAM.id,
        org_player_ids=[],
        identity=identity(),
    )

    assert slot.team == TEAM
    assert slot.author_name == TEAM.name


@pytest.mark.asyncio
async def test_only_the_captain_signs_their_team_up():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    season = await publish(dao, announcer)

    with pytest.raises(exceptions.SlotAuthorInvalid):
        await TakeSlotInteractor(dao=dao, announcer=announcer)(
            YEAR,
            season.slots[0].id,
            author_kind=season_dto.SlotAuthorKind.team,
            team_id=TEAM.id,
            org_player_ids=[],
            identity=identity(OTHER),
        )


@pytest.mark.asyncio
async def test_the_engine_admin_signs_up_a_team_they_do_not_captain():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    season = await publish(dao, announcer)

    slot = await TakeSlotInteractor(dao=dao, announcer=announcer)(
        YEAR,
        season.slots[0].id,
        author_kind=season_dto.SlotAuthorKind.team,
        team_id=TEAM.id,
        org_player_ids=[],
        identity=identity(OTHER, superuser=True),
    )

    assert slot.team == TEAM
    # the change reads like any other: it names the actor, not a role
    assert dao.changes[-1].actor_id == OTHER.id
    assert dao.changes[-1].payload["author"] == TEAM.name


@pytest.mark.asyncio
async def test_a_date_can_be_handed_to_another_author():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    season = await publish(dao, announcer)
    taker = TakeSlotInteractor(dao=dao, announcer=announcer)
    await taker(
        YEAR,
        season.slots[0].id,
        author_kind=season_dto.SlotAuthorKind.player,
        team_id=None,
        org_player_ids=[],
        identity=identity(),
    )

    slot = await taker(
        YEAR,
        season.slots[0].id,
        author_kind=season_dto.SlotAuthorKind.player,
        team_id=None,
        org_player_ids=[],
        identity=identity(OTHER),
    )

    assert slot.owner == OTHER


@pytest.mark.asyncio
async def test_releasing_a_date_frees_it_and_forgets_its_orgs():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    season = await publish(dao, announcer)
    slot_id = season.slots[0].id
    await TakeSlotInteractor(dao=dao, announcer=announcer)(
        YEAR,
        slot_id,
        author_kind=season_dto.SlotAuthorKind.player,
        team_id=None,
        org_player_ids=[OTHER.id],
        identity=identity(),
    )

    released = await ReleaseSlotInteractor(dao=dao, announcer=announcer)(
        YEAR, slot_id, identity=identity()
    )

    assert released.is_free
    assert released.orgs == []


@pytest.mark.asyncio
async def test_another_author_may_free_a_date_and_the_trail_says_who():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    season = await publish(dao, announcer)
    slot_id = season.slots[0].id
    await TakeSlotInteractor(dao=dao, announcer=announcer)(
        YEAR,
        slot_id,
        author_kind=season_dto.SlotAuthorKind.player,
        team_id=None,
        org_player_ids=[],
        identity=identity(),
    )

    released = await ReleaseSlotInteractor(dao=dao, announcer=announcer)(
        YEAR, slot_id, identity=identity(OTHER)
    )

    assert released.is_free
    assert dao.changes[-1].actor_id == OTHER.id


@pytest.mark.asyncio
async def test_the_orgs_of_a_date_can_be_changed_on_their_own():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    season = await publish(dao, announcer)

    slot = await SetSlotOrgsInteractor(dao=dao, announcer=announcer)(
        YEAR, season.slots[0].id, [PLAIN.id], identity=identity()
    )

    # being an org needs no promotion
    assert [org.id for org in slot.orgs] == [PLAIN.id]
    assert dao.changes[0].type == season_dto.ChangeType.slot_orgs_changed


# ---------- the game link ----------


@pytest.mark.asyncio
async def test_linking_a_game_takes_the_date_for_its_author_and_moves_it():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    season = await publish(dao, announcer)

    slot = await LinkGameToSlotInteractor(dao=dao, announcer=announcer)(
        YEAR, season.slots[0].id, GAME.id, identity=identity()
    )

    assert slot.game is not None
    assert slot.owner == GAME.author
    assert slot.date == GAME.start_at.astimezone(tz_game).date()
    assert [change.type for change in dao.changes] == [
        season_dto.ChangeType.slot_game_linked,
        season_dto.ChangeType.slot_moved,
    ]


@pytest.mark.asyncio
async def test_one_game_sits_in_one_date():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    season = await publish(dao, announcer)
    linker = LinkGameToSlotInteractor(dao=dao, announcer=announcer)
    await linker(YEAR, season.slots[0].id, GAME.id, identity=identity())

    with pytest.raises(exceptions.GameAlreadyInSchedule):
        await linker(YEAR, season.slots[1].id, GAME.id, identity=identity())


@pytest.mark.asyncio
async def test_a_linked_date_cannot_be_released_before_it_is_unlinked():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    season = await publish(dao, announcer)
    slot_id = season.slots[0].id
    await LinkGameToSlotInteractor(dao=dao, announcer=announcer)(
        YEAR, slot_id, GAME.id, identity=identity()
    )

    with pytest.raises(exceptions.SlotAlreadyLinked):
        await ReleaseSlotInteractor(dao=dao, announcer=announcer)(
            YEAR, slot_id, identity=identity()
        )

    unlinked = await UnlinkGameFromSlotInteractor(dao=dao, announcer=announcer)(
        YEAR, slot_id, identity=identity()
    )
    assert unlinked.game is None
    assert dao.changes[-1].type == season_dto.ChangeType.slot_game_unlinked


@pytest.mark.asyncio
async def test_unlinking_a_date_that_holds_no_game_does_nothing():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    season = await publish(dao, announcer)

    await UnlinkGameFromSlotInteractor(dao=dao, announcer=announcer)(
        YEAR, season.slots[0].id, identity=identity()
    )

    assert dao.changes == []


@pytest.mark.asyncio
async def test_a_replanned_game_drags_its_date_along():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    season = await publish(dao, announcer)
    slot_id = season.slots[0].id
    await LinkGameToSlotInteractor(dao=dao, announcer=announcer)(
        YEAR, slot_id, GAME.id, identity=identity()
    )
    dao.changes.clear()
    moved_game = dto.Game(
        id=GAME.id,
        author=AUTHOR,
        name=GAME.name,
        status=GAME.status,
        manage_token=GAME.manage_token,
        start_at=datetime(YEAR, 5, 24, 20, tzinfo=tz_game),
        number=None,
        results=GAME.results,
    )

    in_schedule = await SyncLinkedSlotInteractor(dao=dao, announcer=announcer)(moved_game, AUTHOR)

    assert in_schedule is True
    assert (await dao.get_slot(slot_id)).date == date(YEAR, 5, 24)
    assert dao.changes[0].payload["reason"] == "game_rescheduled"


@pytest.mark.asyncio
async def test_a_game_in_no_date_is_out_of_schedule():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    await publish(dao, announcer)

    assert await SyncLinkedSlotInteractor(dao=dao, announcer=announcer)(GAME, AUTHOR) is False


@pytest.mark.asyncio
async def test_a_game_with_no_start_is_out_of_schedule():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    unplanned = dto.Game(
        id=GAME.id,
        author=AUTHOR,
        name=GAME.name,
        status=GAME.status,
        manage_token=GAME.manage_token,
        start_at=None,
        number=None,
        results=GAME.results,
    )

    assert await SyncLinkedSlotInteractor(dao=dao, announcer=announcer)(unplanned, AUTHOR) is False


@pytest.mark.asyncio
async def test_dates_are_suggested_near_a_planned_start():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    await publish(dao, announcer)

    found = await FindSlotsNearGameStartInteractor(dao=dao)(
        datetime(YEAR, 5, 16, 20, tzinfo=tz_game), identity()
    )

    assert [slot.date for slot in found] == [FIRST]


@pytest.mark.asyncio
async def test_a_year_with_no_season_suggests_nothing():
    found = await FindSlotsNearGameStartInteractor(dao=make_dao())(
        datetime(YEAR, 5, 16, 20, tzinfo=tz_game), identity()
    )

    assert found == []


# ---------- the daily digest ----------


@pytest.mark.asyncio
async def test_the_digest_collapses_marks_published_and_notifies():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    season = await publish(dao, announcer)
    slot_id = season.slots[0].id
    mover = MoveSlotInteractor(dao=dao, announcer=announcer)
    await mover(YEAR, slot_id, date(YEAR, 5, 16), identity=identity())
    await mover(YEAR, slot_id, date(YEAR, 5, 17), identity=identity())
    dao.notifications.clear()

    await PublishSeasonDigestInteractor(dao=dao, announcer=announcer)(NOW)

    assert all(change.published_at is not None for change in dao.changes)
    _, digests = announcer.digests[0]
    assert len(digests) == 1
    assert digests[0].date_before == FIRST
    assert digests[0].date_after == date(YEAR, 5, 17)
    assert dao.notifications[0].payload == {"year": YEAR, "changes": 1}


@pytest.mark.asyncio
async def test_changes_that_cancel_out_are_still_marked_but_said_nothing_about():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    season = await publish(dao, announcer)
    slot_id = season.slots[0].id
    mover = MoveSlotInteractor(dao=dao, announcer=announcer)
    await mover(YEAR, slot_id, date(YEAR, 5, 16), identity=identity())
    await mover(YEAR, slot_id, FIRST, identity=identity())
    dao.notifications.clear()

    await PublishSeasonDigestInteractor(dao=dao, announcer=announcer)(NOW)

    assert all(change.published_at is not None for change in dao.changes)
    assert announcer.digests == []
    assert dao.notifications == []


@pytest.mark.asyncio
async def test_a_quiet_day_says_nothing():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    await publish(dao, announcer)

    await PublishSeasonDigestInteractor(dao=dao, announcer=announcer)(NOW)

    assert announcer.digests == []
    assert dao.notifications == []


@pytest.mark.asyncio
async def test_a_finished_season_is_unpinned_once():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    await PublishSeasonInteractor(dao=dao, announcer=announcer)(
        2020, [season_dto.SlotDraft(date=date(2020, 5, 16))], identity=identity()
    )
    announcer.clear()
    digest = PublishSeasonDigestInteractor(dao=dao, announcer=announcer)

    await digest(NOW)

    assert [one.year for one in announcer.closed] == [2020]
    assert (await dao.get_season(2020)).unpinned_at is not None

    announcer.clear()
    await digest(NOW)
    assert announcer.closed == []


@pytest.mark.asyncio
async def test_a_season_still_running_keeps_its_pin():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    await publish(dao, announcer)

    await PublishSeasonDigestInteractor(dao=dao, announcer=announcer)(NOW - timedelta(days=1))

    assert announcer.closed == []
    assert (await dao.get_season(YEAR)).unpinned_at is None


@pytest.mark.asyncio
async def test_a_failed_digest_post_still_marks_the_changes():
    class Refusing(SeasonAnnouncerMock):
        async def announce_digest(self, season, digests):
            raise RuntimeError("telegram said no")

    dao, announcer = make_dao(), Refusing()
    season = await publish(dao, announcer)
    await MoveSlotInteractor(dao=dao, announcer=announcer)(
        YEAR, season.slots[0].id, date(YEAR, 5, 16), identity=identity()
    )

    await PublishSeasonDigestInteractor(dao=dao, announcer=announcer)(NOW)

    assert all(change.published_at is not None for change in dao.changes)


@pytest.mark.asyncio
async def test_every_change_records_who_made_it():
    dao, announcer = make_dao(), SeasonAnnouncerMock()
    season = await publish(dao, announcer)

    await RemoveSlotInteractor(dao=dao, announcer=announcer)(
        YEAR, season.slots[0].id, identity=identity(OTHER)
    )

    # no admin flag to set: the trail names the author who did it
    assert dao.changes[-1].actor_id == OTHER.id
