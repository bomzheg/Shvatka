from collections.abc import Collection, Sequence
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from shvatka.core.models.enums.notification import NotificationType, NotificationSeverity
from shvatka.core.notifications import dto
from shvatka.core.notifications.interactors import (
    ListNotificationsInteractor,
    UnreadCountInteractor,
    MarkNotificationsReadInteractor,
    MarkAllNotificationsReadInteractor,
)


class FakeIdentity:
    def __init__(self, player_id: int) -> None:
        self._player = SimpleNamespace(id=player_id)

    async def get_required_player(self):
        return self._player


class FakeNotificationDao:
    def __init__(self) -> None:
        self.rows: list[dto.Notification] = []
        self.read_calls: list[tuple[int, list[int]]] = []
        self.all_read_calls: list[int] = []
        self.commits = 0
        self.last_get_kwargs: dict = {}

    async def get_for_player(
        self, player_id, *, unread_only=False, limit=50, offset=0
    ) -> Sequence[dto.Notification]:
        self.last_get_kwargs = {
            "player_id": player_id,
            "unread_only": unread_only,
            "limit": limit,
            "offset": offset,
        }
        return [r for r in self.rows if r.recipient_id == player_id]

    async def count_unread(self, player_id) -> int:
        return sum(1 for r in self.rows if r.recipient_id == player_id and not r.is_read)

    async def mark_read(self, player_id, notification_ids: Collection[int]) -> None:
        self.read_calls.append((player_id, list(notification_ids)))

    async def mark_all_read(self, player_id) -> None:
        self.all_read_calls.append(player_id)

    async def commit(self) -> None:
        self.commits += 1


def _notification(id_: int, recipient_id: int, read: bool = False) -> dto.Notification:
    return dto.Notification(
        id=id_,
        recipient_id=recipient_id,
        type=NotificationType.player_joined_team,
        severity=NotificationSeverity.low,
        created_at=datetime(2026, 7, 4, tzinfo=timezone.utc),
        read_at=datetime(2026, 7, 4, tzinfo=timezone.utc) if read else None,
    )


@pytest.mark.asyncio
async def test_list_returns_only_my_notifications() -> None:
    dao = FakeNotificationDao()
    dao.rows = [_notification(1, 42), _notification(2, 99), _notification(3, 42)]
    page = await ListNotificationsInteractor(dao)(FakeIdentity(42), unread_only=True)
    assert {n.id for n in page.items} == {1, 3}
    assert page.limit == 50
    assert page.offset == 0
    assert page.filters == {"unread_only": True}


@pytest.mark.asyncio
async def test_list_clamps_limit_and_offset() -> None:
    dao = FakeNotificationDao()
    await ListNotificationsInteractor(dao)(FakeIdentity(42), limit=9999, offset=-5)
    assert dao.last_get_kwargs["limit"] == 100
    assert dao.last_get_kwargs["offset"] == 0


@pytest.mark.asyncio
async def test_unread_count() -> None:
    dao = FakeNotificationDao()
    dao.rows = [_notification(1, 42), _notification(2, 42, read=True), _notification(3, 42)]
    assert await UnreadCountInteractor(dao)(FakeIdentity(42)) == 2


@pytest.mark.asyncio
async def test_mark_read_commits() -> None:
    dao = FakeNotificationDao()
    await MarkNotificationsReadInteractor(dao)(FakeIdentity(42), [1, 2])
    assert dao.read_calls == [(42, [1, 2])]
    assert dao.commits == 1


@pytest.mark.asyncio
async def test_mark_all_read_commits() -> None:
    dao = FakeNotificationDao()
    await MarkAllNotificationsReadInteractor(dao)(FakeIdentity(42))
    assert dao.all_read_calls == [42]
    assert dao.commits == 1
