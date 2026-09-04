from __future__ import annotations

import asyncio
import enum
import json
import logging
import typing
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Any

from pywebpush import WebPushException, webpush

from shvatka.api.app.config.models.push import PushConfig
from shvatka.infrastructure.db.dao.rdb.push_subscription import PushSubscriptionDAO
from shvatka.infrastructure.db.models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)


class PushUrgency(enum.StrEnum):
    """RFC 8030 urgency: how much battery the push is worth to the receiver.

    Anything below ``high`` is the sender's permission to hold the message until
    the device wakes up on its own, which android does readily — a backgrounded
    browser in doze gets its pushes at the next maintenance window, minutes to
    tens of minutes later. Only ``high`` asks for delivery now.
    """

    very_low = "very-low"
    low = "low"
    normal = "normal"
    high = "high"


# In-game news goes stale in minutes: a hint delivered after the level is over is
# noise, so let the push service drop it rather than wake the phone for it.
IN_GAME_TTL = 10 * 60
# Team news keeps: whoever joined is still on the team tomorrow. A phone that was
# off all evening should get it when it comes back.
TEAM_TTL = 24 * 60 * 60


@dataclass(frozen=True, slots=True)
class PushMessage:
    title: str
    body: str
    url: str = "/"
    tag: str | None = None
    data: dict[str, Any] | None = None
    # How hard the push service should try, as opposed to what the push says.
    # Never part of ``to_json``: the browser is not told any of this.
    urgency: PushUrgency = PushUrgency.normal
    ttl: int = IN_GAME_TTL

    def to_json(self) -> str:
        payload: dict[str, Any] = {
            "title": self.title,
            "body": self.body,
            "url": self.url,
        }
        if self.tag is not None:
            payload["tag"] = self.tag
        if self.data is not None:
            payload["data"] = self.data
        return json.dumps(payload, ensure_ascii=False)


@dataclass(frozen=True, slots=True)
class _Recipient:
    id: int
    endpoint: str
    p256dh: str
    auth: str


@dataclass(slots=True)
class WebPushSender:
    config: PushConfig
    dao: PushSubscriptionDAO

    # a push is a blocking https call in a thread; the bound keeps the pool sane
    PARALLEL: typing.ClassVar[int] = 10

    async def send_to_players(self, player_ids: Collection[int], message: PushMessage) -> None:
        if not self.config.is_configured:
            logger.debug("web push is disabled or not configured")
            return
        if not player_ids:
            return
        subscriptions = await self.dao.get_enabled_for_players(player_ids)
        await self.send_many(subscriptions, message)

    async def send_many(
        self, subscriptions: Sequence[PushSubscription], message: PushMessage
    ) -> None:
        if not subscriptions:
            return
        recipients = [
            _Recipient(
                id=subscription.id,
                endpoint=subscription.endpoint,
                p256dh=subscription.p256dh,
                auth=subscription.auth,
            )
            for subscription in subscriptions
        ]
        semaphore = asyncio.Semaphore(self.PARALLEL)
        expired = await asyncio.gather(
            *(self._send_one(semaphore, recipient, message) for recipient in recipients)
        )
        await self._disable(
            [
                recipient
                for recipient, is_expired in zip(recipients, expired, strict=False)
                if is_expired
            ]
        )

    async def _send_one(
        self, semaphore: asyncio.Semaphore, recipient: _Recipient, message: PushMessage
    ) -> bool:
        try:
            async with semaphore:
                await asyncio.to_thread(self._send_sync, recipient, message)
        except WebPushException as e:
            if e.response is not None and e.response.status_code in {404, 410}:
                return True
            logger.warning("web push provider rejected subscription %s", recipient.id, exc_info=e)
        except Exception as e:  # noqa: BLE001  # one bad subscription must not stop the rest
            logger.warning("web push send failed for subscription %s", recipient.id, exc_info=e)
        return False

    async def _disable(self, expired: Sequence[_Recipient]) -> None:
        if not expired:
            return
        for recipient in expired:
            await self.dao.disable_by_endpoint(recipient.endpoint)
            logger.info("disabled expired web push subscription %s", recipient.id)
        await self.dao.commit()

    def _send_sync(self, recipient: _Recipient, message: PushMessage) -> None:
        webpush(
            subscription_info={
                "endpoint": recipient.endpoint,
                "keys": {
                    "p256dh": recipient.p256dh,
                    "auth": recipient.auth,
                },
            },
            data=message.to_json(),
            vapid_private_key=self.config.vapid_private_key,
            vapid_claims={"sub": self.config.vapid_claims_sub},
            ttl=message.ttl,
            headers={"Urgency": message.urgency.value},
        )
