from collections.abc import Sequence
from datetime import datetime
from types import SimpleNamespace

import pytest

from shvatka.core.models import dto
from shvatka.core.models.enums.chat_type import ChatType
from shvatka.core.models.enums.request import RequestType, RequestStatus
from shvatka.core.notifications import dto as ndto
from shvatka.core.interfaces.bus import ActionRequestResolved
from shvatka.core.notifications import request_interactors
from shvatka.core.notifications.request_interactors import (
    CreateTeamJoinInviteInteractor,
    CreateTeamJoinRequestInteractor,
    CreateTeamMergeRequestInteractor,
    CreatePlayerMergeRequestInteractor,
    CancelRequestInteractor,
    DeclineRequestInteractor,
    AcceptRequestInteractor,
    ListRequestsInteractor,
)
from shvatka.core.players.dto import TimelineItem
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.utils.exceptions import (
    NotAuthorizedForAdmin,
    RequestNotPending,
    RequestPermissionError,
)


def _player(id_: int, username: str = "p") -> dto.Player:
    return dto.Player(id=id_, can_be_author=False, is_dummy=False, username=username)


def _team(captain: dto.Player | None = None, id_: int = 1, name: str = "Gryffindor") -> dto.Team:
    return dto.Team(
        id=id_,
        name=name,
        captain=captain,
        is_dummy=False,
        description=None,
        chat=dto.Chat(tg_id=-100, type=ChatType.group, title="t"),
    )


class FakeIdentity:
    def __init__(
        self, player: dto.Player, team: dto.Team | None = None, superuser: bool = False
    ) -> None:
        self._player = player
        self._team = team
        self._superuser = superuser

    async def get_required_player(self) -> dto.Player:
        return self._player

    async def get_team(self) -> dto.Team | None:
        return self._team

    async def get_superuser(self) -> dto.Player:
        if not self._superuser:
            raise NotAuthorizedForAdmin(player=self._player)
        return self._player

    async def is_superuser(self) -> bool:
        return self._superuser


class FakeRequests:
    def __init__(self) -> None:
        self.rows: dict[int, ndto.ActionRequest] = {}
        self.pending: ndto.ActionRequest | None = None
        self.commits = 0
        self._next = 1

    async def create(self, **kwargs) -> ndto.ActionRequest:
        request = ndto.ActionRequest(
            id=self._next,
            type=kwargs["type_"],
            status=RequestStatus.pending,
            initiator_id=kwargs["initiator_id"],
            created_at=datetime.now(tz=tz_utc),
            payload=kwargs.get("payload") or {},
            target_player_id=kwargs.get("target_player_id"),
            team_id=kwargs.get("team_id"),
            game_id=kwargs.get("game_id"),
        )
        self.rows[self._next] = request
        self._next += 1
        return request

    async def get_pending(self, **kwargs) -> ndto.ActionRequest | None:
        return self.pending

    async def get_by_id(self, request_id: int) -> ndto.ActionRequest:
        return self.rows[request_id]

    async def set_status(self, request_id, status, *, responder_id=None) -> ndto.ActionRequest:
        request = self.rows[request_id]
        request.status = status
        request.responder_id = responder_id
        return request

    async def commit(self) -> None:
        self.commits += 1

    async def add_bot_message(self, request_id: int, *, chat_id: int, message_id: int) -> None:
        pass

    async def get_incoming(self, player_id: int, *, only_pending: bool = False):
        return [
            request
            for request in self.rows.values()
            if request.target_player_id == player_id and (not only_pending or request.is_pending)
        ]

    async def get_pending_for_teams(self, team_ids):
        return []

    async def get_pending_by_types(self, types):
        return [
            request
            for request in self.rows.values()
            if request.type in types and request.is_pending
        ]


class FakeNotifier:
    def __init__(self) -> None:
        self.created: list[ndto.ActionRequest] = []

    async def notify_created(self, request: ndto.ActionRequest) -> None:
        self.created.append(request)


class FakeBus:
    def __init__(self) -> None:
        self.events: list[object] = []

    async def submit(self, event: object) -> None:
        self.events.append(event)


class FakeNotifications:
    def __init__(self) -> None:
        self.created: list[dict] = []
        self.bulk: list[dict] = []

    async def create(self, **kwargs) -> ndto.Notification:
        self.created.append(kwargs)
        return SimpleNamespace(id=1)  # type: ignore[return-value]

    async def create_for_recipients(self, **kwargs) -> None:
        self.bulk.append(kwargs)

    async def commit(self) -> None:
        pass


class FakeTeamDao:
    def __init__(self, team: dto.Team, *more: dto.Team) -> None:
        self._teams = {t.id: t for t in (team, *more)}
        self._team = team

    async def get_by_id(self, team_id: int) -> dto.Team:
        return self._teams.get(team_id, self._team)


class FakeSuperusers:
    def __init__(self, player_ids: set[int]) -> None:
        self._player_ids = player_ids

    async def get_superuser_player_ids(self) -> set[int]:
        return self._player_ids


class FakePlayerDao:
    def __init__(self, players: dict[int, dto.Player]) -> None:
        self._players = players

    async def get_by_id(self, player_id: int) -> dto.Player:
        return self._players[player_id]


class FakeTeamPlayersDao:
    def __init__(self, members: Sequence) -> None:
        self._members = members

    async def get_players(self, team):
        return self._members


def _member(player: dto.Player, *, captain: bool, can_add: bool):
    return SimpleNamespace(player=player, is_captain=captain, can_add_players=can_add)


@pytest.mark.asyncio
async def test_create_team_join_invite() -> None:
    cap = _player(1, "cap")
    target = _player(2, "target")
    team = _team(cap)
    requests = FakeRequests()
    notifications = FakeNotifications()
    interactor = CreateTeamJoinInviteInteractor(
        requests=requests,
        notifications=notifications,
        team_dao=FakeTeamDao(team),
        player_dao=FakePlayerDao({2: target}),
        team_player_dao=SimpleNamespace(),
        notifier=FakeNotifier(),
    )
    request = await interactor(FakeIdentity(cap), team_id=1, player_id=2, role="chaser")
    assert request.type == RequestType.team_join_invite
    assert request.target_player_id == 2
    assert requests.commits == 1
    assert notifications.created[0]["recipient_id"] == 2
    assert notifications.created[0]["request_id"] == request.id


@pytest.mark.asyncio
async def test_create_team_join_invite_is_idempotent() -> None:
    cap = _player(1, "cap")
    target = _player(2, "target")
    team = _team(cap)
    requests = FakeRequests()
    existing = ndto.ActionRequest(
        id=99,
        type=RequestType.team_join_invite,
        status=RequestStatus.pending,
        initiator_id=1,
        created_at=datetime.now(tz=tz_utc),
    )
    requests.pending = existing
    notifications = FakeNotifications()
    interactor = CreateTeamJoinInviteInteractor(
        requests=requests,
        notifications=notifications,
        team_dao=FakeTeamDao(team),
        player_dao=FakePlayerDao({2: target}),
        team_player_dao=SimpleNamespace(),
        notifier=FakeNotifier(),
    )
    request = await interactor(FakeIdentity(cap), team_id=1, player_id=2)
    assert request.id == 99
    assert notifications.created == []
    assert requests.commits == 0


@pytest.mark.asyncio
async def test_create_team_join_request_notifies_managers_only() -> None:
    asker = _player(3, "asker")
    cap = _player(1, "cap")
    manager = _player(4, "manager")
    plain = _player(5, "plain")
    team = _team(cap)
    requests = FakeRequests()
    notifications = FakeNotifications()
    members = [
        _member(cap, captain=True, can_add=False),
        _member(manager, captain=False, can_add=True),
        _member(plain, captain=False, can_add=False),
    ]
    interactor = CreateTeamJoinRequestInteractor(
        requests=requests,
        notifications=notifications,
        team_dao=FakeTeamDao(team),
        team_players_dao=FakeTeamPlayersDao(members),
        notifier=FakeNotifier(),
    )
    request = await interactor(FakeIdentity(asker), team_id=1)
    assert request.type == RequestType.team_join_request
    assert notifications.bulk[0]["recipient_ids"] == {1, 4}  # captain + can_add, not plain


@pytest.mark.asyncio
async def test_cancel_only_by_initiator() -> None:
    requests = FakeRequests()
    requests.rows[1] = ndto.ActionRequest(
        id=1,
        type=RequestType.team_join_invite,
        status=RequestStatus.pending,
        initiator_id=1,
        created_at=datetime.now(tz=tz_utc),
    )
    interactor = CancelRequestInteractor(requests=requests, bus=FakeBus())
    with pytest.raises(RequestPermissionError):
        await interactor(FakeIdentity(_player(2)), request_id=1)
    updated = await interactor(FakeIdentity(_player(1)), request_id=1)
    assert updated.status == RequestStatus.cancelled


@pytest.mark.asyncio
async def test_cancel_rejects_non_pending() -> None:
    requests = FakeRequests()
    requests.rows[1] = ndto.ActionRequest(
        id=1,
        type=RequestType.team_join_invite,
        status=RequestStatus.accepted,
        initiator_id=1,
        created_at=datetime.now(tz=tz_utc),
    )
    with pytest.raises(RequestNotPending):
        await CancelRequestInteractor(requests=requests, bus=FakeBus())(
            FakeIdentity(_player(1)), request_id=1
        )


@pytest.mark.asyncio
async def test_decline_invite_notifies_initiator() -> None:
    target = _player(2, "target")
    requests = FakeRequests()
    requests.rows[1] = ndto.ActionRequest(
        id=1,
        type=RequestType.team_join_invite,
        status=RequestStatus.pending,
        initiator_id=1,
        target_player_id=2,
        created_at=datetime.now(tz=tz_utc),
    )
    notifications = FakeNotifications()
    interactor = DeclineRequestInteractor(
        requests=requests,
        notifications=notifications,
        team_dao=SimpleNamespace(),
        team_player_dao=SimpleNamespace(),
        bus=FakeBus(),
    )
    updated = await interactor(FakeIdentity(target), request_id=1)
    assert updated.status == RequestStatus.declined
    assert notifications.created[0]["recipient_id"] == 1


@pytest.mark.asyncio
async def test_decline_invite_wrong_actor_forbidden() -> None:
    requests = FakeRequests()
    requests.rows[1] = ndto.ActionRequest(
        id=1,
        type=RequestType.team_join_invite,
        status=RequestStatus.pending,
        initiator_id=1,
        target_player_id=2,
        created_at=datetime.now(tz=tz_utc),
    )
    interactor = DeclineRequestInteractor(
        requests=requests,
        notifications=FakeNotifications(),
        team_dao=SimpleNamespace(),
        team_player_dao=SimpleNamespace(),
        bus=FakeBus(),
    )
    with pytest.raises(RequestPermissionError):
        await interactor(FakeIdentity(_player(7)), request_id=1)


def _accept_interactor(
    requests: FakeRequests,
    *,
    notifications: FakeNotifications | None = None,
    team_dao=None,
    player_dao=None,
    bus: FakeBus | None = None,
) -> AcceptRequestInteractor:
    return AcceptRequestInteractor(
        requests=requests,
        notifications=notifications or FakeNotifications(),
        team_joiner=SimpleNamespace(),
        team_dao=team_dao or SimpleNamespace(),
        team_player_dao=SimpleNamespace(),
        player_dao=player_dao or SimpleNamespace(),
        org_adder=SimpleNamespace(),
        team_merger=SimpleNamespace(),
        player_merger=SimpleNamespace(),
        game_log=SimpleNamespace(),
        team_notifier=SimpleNamespace(),
        org_notifier=SimpleNamespace(),
        bus=bus or FakeBus(),
    )


@pytest.mark.asyncio
async def test_accept_rejects_non_pending() -> None:
    requests = FakeRequests()
    requests.rows[1] = ndto.ActionRequest(
        id=1,
        type=RequestType.team_join_invite,
        status=RequestStatus.cancelled,
        initiator_id=1,
        target_player_id=2,
        created_at=datetime.now(tz=tz_utc),
    )
    interactor = _accept_interactor(requests)
    with pytest.raises(RequestNotPending):
        await interactor(FakeIdentity(_player(2)), request_id=1)


@pytest.mark.asyncio
async def test_accept_invite_wrong_actor_forbidden() -> None:
    requests = FakeRequests()
    requests.rows[1] = ndto.ActionRequest(
        id=1,
        type=RequestType.team_join_invite,
        status=RequestStatus.pending,
        initiator_id=1,
        target_player_id=2,
        team_id=1,
        created_at=datetime.now(tz=tz_utc),
    )
    interactor = _accept_interactor(
        requests, team_dao=FakeTeamDao(_team()), player_dao=FakePlayerDao({1: _player(1)})
    )
    with pytest.raises(RequestPermissionError):
        await interactor(FakeIdentity(_player(7)), request_id=1)


@pytest.mark.asyncio
async def test_create_team_merge_request() -> None:
    cap = _player(1, "cap")
    primary = _team(cap, id_=1, name="Gryffindor")
    secondary = _team(None, id_=2, name="Gryffindor (forum)")
    requests = FakeRequests()
    notifications = FakeNotifications()
    notifier = FakeNotifier()
    interactor = CreateTeamMergeRequestInteractor(
        requests=requests,
        notifications=notifications,
        team_dao=FakeTeamDao(primary, secondary),
        superusers=FakeSuperusers({10, 11}),
        notifier=notifier,
    )
    request = await interactor(FakeIdentity(cap), primary_team_id=1, secondary_team_id=2)
    assert request.type == RequestType.team_merge
    assert request.team_id == 1
    assert request.payload["secondary_team_id"] == 2
    assert notifications.bulk[0]["recipient_ids"] == {10, 11}
    assert notifications.bulk[0]["request_id"] == request.id
    assert notifier.created == [request]
    assert requests.commits == 1


@pytest.mark.asyncio
async def test_create_team_merge_request_only_by_captain() -> None:
    cap = _player(1, "cap")
    stranger = _player(9, "stranger")
    primary = _team(cap, id_=1)
    interactor = CreateTeamMergeRequestInteractor(
        requests=FakeRequests(),
        notifications=FakeNotifications(),
        team_dao=FakeTeamDao(primary),
        superusers=FakeSuperusers(set()),
        notifier=FakeNotifier(),
    )
    with pytest.raises(RequestPermissionError):
        await interactor(FakeIdentity(stranger), primary_team_id=1, secondary_team_id=2)


@pytest.mark.asyncio
async def test_create_player_merge_request_for_self() -> None:
    player = _player(3, "harry")
    forum_copy = _player(8, "harry_forum")
    requests = FakeRequests()
    notifications = FakeNotifications()
    interactor = CreatePlayerMergeRequestInteractor(
        requests=requests,
        notifications=notifications,
        player_dao=FakePlayerDao({3: player, 8: forum_copy}),
        superusers=FakeSuperusers({10}),
        notifier=FakeNotifier(),
    )
    request = await interactor(FakeIdentity(player), secondary_player_id=8)
    assert request.type == RequestType.player_merge
    assert request.initiator_id == 3
    assert request.target_player_id == 3
    assert request.payload["secondary_player_id"] == 8
    assert notifications.bulk[0]["recipient_ids"] == {10}


@pytest.mark.asyncio
async def test_create_player_merge_request_for_other_requires_admin() -> None:
    actor = _player(3, "harry")
    interactor = CreatePlayerMergeRequestInteractor(
        requests=FakeRequests(),
        notifications=FakeNotifications(),
        player_dao=FakePlayerDao({4: _player(4), 8: _player(8)}),
        superusers=FakeSuperusers(set()),
        notifier=FakeNotifier(),
    )
    with pytest.raises(NotAuthorizedForAdmin):
        await interactor(FakeIdentity(actor), secondary_player_id=8, primary_player_id=4)
    request = await interactor(
        FakeIdentity(actor, superuser=True), secondary_player_id=8, primary_player_id=4
    )
    assert request.target_player_id == 4
    assert request.initiator_id == 3


def _team_merge_request() -> ndto.ActionRequest:
    return ndto.ActionRequest(
        id=1,
        type=RequestType.team_merge,
        status=RequestStatus.pending,
        initiator_id=1,
        team_id=1,
        created_at=datetime.now(tz=tz_utc),
        payload={
            "primary_team_id": 1,
            "secondary_team_id": 2,
            "captain_id": 1,
            "captain_name": "cap",
        },
    )


@pytest.mark.asyncio
async def test_accept_team_merge_requires_superuser() -> None:
    requests = FakeRequests()
    requests.rows[1] = _team_merge_request()
    interactor = _accept_interactor(requests)
    with pytest.raises(NotAuthorizedForAdmin):
        await interactor(FakeIdentity(_player(2)), request_id=1)
    assert requests.rows[1].status == RequestStatus.pending


@pytest.mark.asyncio
async def test_accept_team_merge_performs_merge(monkeypatch: pytest.MonkeyPatch) -> None:
    cap = _player(1, "cap")
    admin = _player(42, "admin")
    primary = _team(cap, id_=1)
    secondary = _team(None, id_=2, name="forum copy")
    requests = FakeRequests()
    requests.rows[1] = _team_merge_request()
    merged = []

    async def fake_merge_teams(manager, primary_, secondary_, game_log, dao):
        merged.append((manager, primary_, secondary_))

    monkeypatch.setattr(request_interactors, "merge_teams", fake_merge_teams)
    notifications = FakeNotifications()
    bus = FakeBus()
    interactor = _accept_interactor(
        requests,
        notifications=notifications,
        team_dao=FakeTeamDao(primary, secondary),
        player_dao=FakePlayerDao({1: cap}),
        bus=bus,
    )
    updated = await interactor(FakeIdentity(admin, superuser=True), request_id=1)
    assert updated.status == RequestStatus.accepted
    assert updated.responder_id == 42
    assert merged == [(cap, primary, secondary)]
    assert notifications.created[0]["recipient_id"] == 1
    assert bus.events == [ActionRequestResolved(request_id=1)]


@pytest.mark.asyncio
async def test_accept_player_merge_performs_merge(monkeypatch: pytest.MonkeyPatch) -> None:
    player = _player(3, "harry")
    forum_copy = _player(8, "harry_forum")
    admin = _player(42, "admin")
    requests = FakeRequests()
    requests.rows[1] = ndto.ActionRequest(
        id=1,
        type=RequestType.player_merge,
        status=RequestStatus.pending,
        initiator_id=3,
        target_player_id=3,
        created_at=datetime.now(tz=tz_utc),
        payload={"primary_player_id": 3, "secondary_player_id": 8},
    )
    merged = []

    async def fake_merge_players(primary, secondary, game_log, dao, timeline=None):
        merged.append((primary, secondary, timeline))

    monkeypatch.setattr(request_interactors, "merge_players", fake_merge_players)
    bus = FakeBus()
    interactor = _accept_interactor(
        requests, player_dao=FakePlayerDao({3: player, 8: forum_copy}), bus=bus
    )
    updated = await interactor(FakeIdentity(admin, superuser=True), request_id=1)
    assert updated.status == RequestStatus.accepted
    assert merged == [(player, forum_copy, None)]
    assert bus.events == [ActionRequestResolved(request_id=1)]


@pytest.mark.asyncio
async def test_accept_player_merge_forwards_timeline(monkeypatch: pytest.MonkeyPatch) -> None:
    player = _player(3, "harry")
    forum_copy = _player(8, "harry_forum")
    admin = _player(42, "admin")
    requests = FakeRequests()
    requests.rows[1] = ndto.ActionRequest(
        id=1,
        type=RequestType.player_merge,
        status=RequestStatus.pending,
        initiator_id=3,
        target_player_id=3,
        created_at=datetime.now(tz=tz_utc),
        payload={"primary_player_id": 3, "secondary_player_id": 8},
    )
    passed_timelines = []

    async def fake_merge_players(primary, secondary, game_log, dao, timeline=None):
        passed_timelines.append(timeline)

    monkeypatch.setattr(request_interactors, "merge_players", fake_merge_players)
    interactor = _accept_interactor(requests, player_dao=FakePlayerDao({3: player, 8: forum_copy}))
    timeline = [TimelineItem(team_id=1, date_joined=datetime.now(tz=tz_utc))]
    updated = await interactor(
        FakeIdentity(admin, superuser=True), request_id=1, timeline=timeline
    )
    assert updated.status == RequestStatus.accepted
    assert passed_timelines == [timeline]


@pytest.mark.asyncio
async def test_decline_team_merge_requires_superuser() -> None:
    requests = FakeRequests()
    requests.rows[1] = _team_merge_request()
    interactor = DeclineRequestInteractor(
        requests=requests,
        notifications=FakeNotifications(),
        team_dao=SimpleNamespace(),
        team_player_dao=SimpleNamespace(),
        bus=FakeBus(),
    )
    with pytest.raises(NotAuthorizedForAdmin):
        await interactor(FakeIdentity(_player(7)), request_id=1)
    updated = await interactor(FakeIdentity(_player(42), superuser=True), request_id=1)
    assert updated.status == RequestStatus.declined


@pytest.mark.asyncio
async def test_decline_player_merge_by_its_target() -> None:
    requests = FakeRequests()
    requests.rows[1] = ndto.ActionRequest(
        id=1,
        type=RequestType.player_merge,
        status=RequestStatus.pending,
        initiator_id=42,
        target_player_id=3,
        created_at=datetime.now(tz=tz_utc),
        payload={"primary_player_id": 3, "secondary_player_id": 8},
    )
    interactor = DeclineRequestInteractor(
        requests=requests,
        notifications=FakeNotifications(),
        team_dao=SimpleNamespace(),
        team_player_dao=SimpleNamespace(),
        bus=FakeBus(),
    )
    updated = await interactor(FakeIdentity(_player(3)), request_id=1)
    assert updated.status == RequestStatus.declined


@pytest.mark.asyncio
async def test_incoming_includes_merges_for_superuser_only() -> None:
    requests = FakeRequests()
    requests.rows[1] = _team_merge_request()
    interactor = ListRequestsInteractor(requests=requests)
    plain = await interactor.incoming(FakeIdentity(_player(7)))
    assert plain == []
    admin = await interactor.incoming(FakeIdentity(_player(42), superuser=True))
    assert [request.id for request in admin] == [1]
