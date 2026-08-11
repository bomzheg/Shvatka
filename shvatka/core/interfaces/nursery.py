from typing import Any, Awaitable, Callable, Protocol

BackgroundTask = Callable[..., Awaitable[None]]


class Nursery(Protocol):
    """App-scoped supervisor of every detached ("run and forget") task.

    Nothing spawns tasks on its own: work that has to outlive the request that
    asked for it goes through the nursery, so the app keeps a reference to
    everything still running, notices when one of them fails, and can cancel
    them all on shutdown.
    """

    def spawn(self, task: BackgroundTask, /, *args: Any, **kwargs: Any) -> None:
        """Run ``task`` detached from the caller and return immediately.

        ``task`` is an ordinary async function called with the given arguments.
        It runs in a DI scope of its own, so its ``FromDishka[...]`` parameters
        are resolved there and it acquires (and finalizes) its own db session
        and every other request-scoped resource, instead of borrowing the
        caller's — which is closed as soon as the caller returns.
        """
        raise NotImplementedError
