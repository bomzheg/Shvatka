from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Any

from pywebpush import WebPushException, webpush

from shvatka.api.config.models.push import PushConfig
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


@dataclass(slots=True)
class WebPushSender:
    config: PushConfig
    dao: PushSubscriptionDAO

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
        for subscription in subscriptions:
            await self._send_one(subscription, message)

    async def _send_one(self, subscription: PushSubscription, message: PushMessage) -> None:
        try:
            await asyncio.to_thread(self._send_sync, subscription, message)
        except WebPushException as e:
            if e.response is not None and e.response.status_code in {404, 410}:
                await self.dao.disable_by_endpoint(subscription.endpoint)
                await self.dao.commit()
                logger.info("disabled expired web push subscription %s", subscription.id)
                return
            logger.warning(
                "web push provider rejected subscription %s", subscription.id, exc_info=e
            )
        except Exception as e:
            logger.warning("web push send failed for subscription %s", subscription.id, exc_info=e)

    def _send_sync(self, subscription: PushSubscription, message: PushMessage) -> None:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh,
                    "auth": subscription.auth,
                },
            },
            data=message.to_json(),
            vapid_private_key=self.config.vapid_private_key,
            vapid_claims={"sub": self.config.vapid_claims_sub},
            ttl=10 * 60,
        )
