from typing import Any

from shvatka.core.interfaces.nursery import BackgroundTask, Nursery
from shvatka.tgbot.tasks import BotSenders
from shvatka.tgbot.views.outbox import BotOutbox


class FakeNursery(Nursery):
    """Remembers what was spawned instead of running it."""

    def __init__(self) -> None:
        self.spawned: list[tuple[BackgroundTask, dict[str, Any]]] = []

    def spawn(self, task: BackgroundTask, /, *args: Any, **kwargs: Any) -> None:
        self.spawned.append((task, kwargs))


async def deliver_recorded(
    outbox: BotOutbox,
    *,
    view: Any = None,
    org_notifier: Any = None,
    game_log: Any = None,
) -> None:
    """Show what the outbox recorded, as the delivery task does in the app."""
    senders = BotSenders(view=view, org_notifier=org_notifier, game_log=game_log)
    for call in outbox.calls:
        await call(senders)
