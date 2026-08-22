"""What the bot has to show, collected during a request and shown after it."""

import logging
from dataclasses import dataclass, field

from shvatka.core.interfaces.nursery import Nursery
from shvatka.tgbot.tasks import BotDelivery, deliver_bot_views

logger = logging.getLogger(__name__)


@dataclass
class BotOutbox:
    """The bot-side view calls of one request, delivered once it is over.

    Telegram is slow on purpose: a puzzle is a caption and several hints, a
    second apart (:class:`~shvatka.tgbot.views.hint_sender.HintSender`), and
    orgs are notified one message at a time. A player typing a key from the
    site used to wait for all of it before the api answered — seconds of it on
    a level up.

    Nothing in that fan-out is part of the answer: the response is built from
    the :class:`~shvatka.core.views.game.InputContainer` the web view fills
    in memory. So the bot half is recorded here instead of awaited, and
    :meth:`flush` hands the whole recording to the nursery as **one** task
    (:func:`~shvatka.tgbot.tasks.deliver_bot_views`) when the request's scope
    closes — one task, so the messages of one key keep their order.

    What is recorded is a call over plain domain dtos and aiogram messages,
    never a sender: the senders belong to the task's own scope, and the task
    resolves them there.
    """

    nursery: Nursery
    calls: list[BotDelivery] = field(default_factory=list)

    def add(self, call: BotDelivery) -> None:
        self.calls.append(call)

    def flush(self) -> None:
        """Hand what was recorded to the nursery and forget it.

        Called when the request's di scope closes, so every entry point (the
        api, the bot itself, a scheduled job) delivers without having to
        remember to.
        """
        if not self.calls:
            return
        calls = tuple(self.calls)
        self.calls.clear()
        logger.debug("delivering %s bot view calls in background", len(calls))
        self.nursery.spawn(deliver_bot_views, calls=calls)
