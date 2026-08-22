from __future__ import annotations

import asyncio
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


@dataclass(frozen=True, slots=True)
class PushMessage:
    title: str
    body: str
    url: str = "/"
    tag: str | None = None
    data: dict[str, Any] | None = None

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
    """The subscription as the sending thread sees it: plain values only.

    The orm object stays on the event loop — reading its attributes from a
    worker thread could emit a query on a session another coroutine is using.
    """

    id: int
    endpoint: str
    p256dh: str
    auth: str


@dataclass(slots=True)
class WebPushSender:
    config: PushConfig
    dao: PushSubscriptionDAO

    PARALLEL: typing.ClassVar[int] = 10
    """How many pushes are in flight at once.

    A push is a blocking https call handed to a thread, so sending a level to a
    team of ten used to cost ten round trips in a row — on the request the
    player is waiting for. They are independent, so they go together; the bound
    keeps the thread pool (and the push provider) out of trouble.
    """

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
            [recipient for recipient, is_expired in zip(recipients, expired) if is_expired]
        )

    async def _send_one(
        self, semaphore: asyncio.Semaphore, recipient: _Recipient, message: PushMessage
    ) -> bool:
        """Send one push; tell whether the subscription is gone for good.

        Disabling it is left to the caller: the dao lives on the request's
        session, which only one coroutine at a time may touch.
        """
        try:
            async with semaphore:
                await asyncio.to_thread(self._send_sync, recipient, message)
        except WebPushException as e:
            if e.response is not None and e.response.status_code in {404, 410}:
                return True
            logger.warning("web push provider rejected subscription %s", recipient.id, exc_info=e)
        except Exception as e:
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
            ttl=10 * 60,
        )
