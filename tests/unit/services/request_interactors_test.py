from collections.abc import Sequence
from datetime import datetime
from types import SimpleNamespace

import pytest

from shvatka.core.models import dto
from shvatka.core.models.enums.chat_type import ChatType
from shvatka.core.models.enums.request import RequestType, RequestStatus
from shvatka.core.notifications import dto as ndto
from shvatka.core.notifications.request_interactors import (
    CreateTeamJoinInviteInteractor,
    CreateTeamJoinRequestInteractor,
    CancelRequestInteractor,
    DeclineRequestInteractor,
    AcceptRequestInteractor,
)
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.utils.exceptions import RequestNotPending, RequestPermissionError


def _player(id_: int, username: str = "p") -> dto.Player:
    return dto.Player(id=id_, can_be_author=False, is_dummy=False, username=username)


def _team(captain: dto.Player | None = None) -> dto.Team:
    return dto.Team(
        id=1,
        name="Gryffindor",
        captain=captain,
        is_dummy=False,
        description=None,
        chat=dto.Chat(tg_id=-100, type=ChatType.group, title="t"),
    )


class FakeIdentity:
    def __init__(self, player: dto.Player, team: dto.Team | None = None) -> None:
        self._player = player
        self._team = team

    async def get_required_player(self) -> dto.Player:
        return self._player

    async def get_team(self) -> dto.Team | None:
        return self._team


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

    async def add_bot_message(
        self, request_id: int, *, chat_id: int, message_id: int
    ) -> ndto.ActionRequest:
        request = self.rows[request_id]
        request.bot_messages.append({"chat_id": chat_id, "message_id": message_id})
        return request


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
    def __init__(self, team: dto.Team) -> None:
        self._team = team

    async def get_by_id(self, team_id: int) -> dto.Team:
        return self._team


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
    interactor = AcceptRequestInteractor(
        requests=requests,
        notifications=FakeNotifications(),
        team_joiner=SimpleNamespace(),
        team_dao=SimpleNamespace(),
        team_player_dao=SimpleNamespace(),
        player_dao=SimpleNamespace(),
        org_adder=SimpleNamespace(),
        team_notifier=SimpleNamespace(),
        org_notifier=SimpleNamespace(),
        bus=FakeBus(),
    )
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
    interactor = AcceptRequestInteractor(
        requests=requests,
        notifications=FakeNotifications(),
        team_joiner=SimpleNamespace(),
        team_dao=FakeTeamDao(_team()),
        team_player_dao=SimpleNamespace(),
        player_dao=FakePlayerDao({1: _player(1)}),
        org_adder=SimpleNamespace(),
        team_notifier=SimpleNamespace(),
        org_notifier=SimpleNamespace(),
        bus=FakeBus(),
    )
    with pytest.raises(RequestPermissionError):
        await interactor(FakeIdentity(_player(7)), request_id=1)
