import time
from types import SimpleNamespace

import pytest
from pywebpush import WebPushException

from shvatka.api.app.config.models.push import PushConfig
from shvatka.api.app.utils import push as push_module
from shvatka.api.app.utils.push import TEAM_TTL, PushMessage, PushUrgency, WebPushSender

CONFIG = PushConfig(
    vapid_public_key="public",
    vapid_private_key="private",
    vapid_claims_sub="mailto:shvatka@example.com",
    enabled=True,
)
MESSAGE = PushMessage(title="Новый уровень", body="открыт уровень 2")


class FakeDao:
    def __init__(self) -> None:
        self.disabled: list[str] = []
        self.commits = 0

    async def disable_by_endpoint(self, endpoint: str) -> None:
        self.disabled.append(endpoint)

    async def commit(self) -> None:
        self.commits += 1


def subscription(number: int):
    return SimpleNamespace(
        id=number,
        endpoint=f"https://push.example.com/{number}",
        p256dh="p256dh",
        auth="auth",
    )


def expired(status_code: int) -> WebPushException:
    return WebPushException("gone", response=SimpleNamespace(status_code=status_code, text="gone"))


@pytest.mark.asyncio
async def test_pushes_go_together_not_one_after_another(monkeypatch) -> None:
    in_flight = 0
    peak = 0

    def slow_webpush(**kwargs) -> None:
        nonlocal in_flight, peak
        in_flight += 1
        peak = max(peak, in_flight)
        time.sleep(0.05)  # the real one blocks on https, in a thread of its own
        in_flight -= 1

    monkeypatch.setattr(push_module, "webpush", slow_webpush)
    sender = WebPushSender(config=CONFIG, dao=FakeDao())

    await sender.send_many([subscription(i) for i in range(5)], MESSAGE)

    assert peak > 1, "a team of players is not pushed to one device at a time"


@pytest.mark.asyncio
async def test_every_subscription_is_pushed_to(monkeypatch) -> None:
    endpoints: list[str] = []
    monkeypatch.setattr(
        push_module,
        "webpush",
        lambda **kwargs: endpoints.append(kwargs["subscription_info"]["endpoint"]),
    )
    sender = WebPushSender(config=CONFIG, dao=FakeDao())

    await sender.send_many([subscription(1), subscription(2)], MESSAGE)

    assert sorted(endpoints) == [
        "https://push.example.com/1",
        "https://push.example.com/2",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [404, 410])
async def test_gone_subscription_is_disabled_once(monkeypatch, status_code: int) -> None:
    def webpush_mock(**kwargs) -> None:
        if kwargs["subscription_info"]["endpoint"].endswith("/2"):
            raise expired(status_code)

    monkeypatch.setattr(push_module, "webpush", webpush_mock)
    dao = FakeDao()
    sender = WebPushSender(config=CONFIG, dao=dao)

    await sender.send_many([subscription(1), subscription(2)], MESSAGE)

    assert dao.disabled == ["https://push.example.com/2"]
    assert dao.commits == 1


@pytest.mark.asyncio
async def test_one_broken_push_does_not_stop_the_others(monkeypatch) -> None:
    delivered: list[str] = []

    def webpush_mock(**kwargs) -> None:
        endpoint = kwargs["subscription_info"]["endpoint"]
        if endpoint.endswith("/1"):
            raise RuntimeError("the provider is down")
        delivered.append(endpoint)

    monkeypatch.setattr(push_module, "webpush", webpush_mock)
    dao = FakeDao()
    sender = WebPushSender(config=CONFIG, dao=dao)

    await sender.send_many([subscription(1), subscription(2)], MESSAGE)

    assert delivered == ["https://push.example.com/2"]
    assert dao.disabled == [], "a provider having a bad day is not an expired subscription"


@pytest.mark.asyncio
async def test_nothing_sent_when_push_is_not_configured(monkeypatch) -> None:
    monkeypatch.setattr(
        push_module, "webpush", lambda **kwargs: pytest.fail("push must stay silent")
    )
    sender = WebPushSender(config=PushConfig(), dao=FakeDao())

    await sender.send_to_players([1, 2], MESSAGE)


@pytest.mark.asyncio
async def test_urgency_and_ttl_reach_the_push_service(monkeypatch) -> None:
    """They are the whole point of the fields: nothing else carries them."""
    sent: list[dict] = []
    monkeypatch.setattr(push_module, "webpush", lambda **kwargs: sent.append(kwargs))
    sender = WebPushSender(config=CONFIG, dao=FakeDao())
    message = PushMessage(
        title="Новая подсказка",
        body="подсказка #1",
        urgency=PushUrgency.high,
        ttl=TEAM_TTL,
    )

    await sender.send_many([subscription(1)], message)

    assert sent[0]["headers"] == {"Urgency": "high"}
    assert sent[0]["ttl"] == 24 * 60 * 60


@pytest.mark.asyncio
async def test_a_push_is_normal_urgency_and_dies_in_ten_minutes_by_default(monkeypatch) -> None:
    sent: list[dict] = []
    monkeypatch.setattr(push_module, "webpush", lambda **kwargs: sent.append(kwargs))
    sender = WebPushSender(config=CONFIG, dao=FakeDao())

    await sender.send_many([subscription(1)], MESSAGE)

    assert sent[0]["headers"] == {"Urgency": "normal"}
    assert sent[0]["ttl"] == 10 * 60


def test_delivery_is_not_told_to_the_browser() -> None:
    """``to_json`` is the payload the service worker sees; urgency is between us
    and the push service.
    """
    message = PushMessage(title="t", body="b", urgency=PushUrgency.high, ttl=TEAM_TTL)

    assert "urgency" not in message.to_json()
    assert "ttl" not in message.to_json()
