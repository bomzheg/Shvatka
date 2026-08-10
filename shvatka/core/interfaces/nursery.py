from typing import Protocol


class BackgroundTask(Protocol):
    """A unit of work detached from whatever asked for it.

    A task is built by the DI container, so everything it needs (a db session,
    views, clients) is injected into ``__init__`` the same way an interactor
    gets its dependencies. The runtime data of a single run is passed as a
    params object to :meth:`Nursery.spawn`.
    """

    async def __call__(self) -> None:
        raise NotImplementedError


class Nursery(Protocol):
    """App-scoped supervisor of every detached ("run and forget") task.

    Nothing spawns tasks on its own: work that has to outlive the request that
    asked for it goes through the nursery, so the app keeps a reference to
    everything still running, notices when one of them fails, and can cancel
    them all on shutdown.
    """

    def spawn(self, task: type[BackgroundTask], params: object) -> None:
        """Run ``task`` detached from the caller and return immediately.

        The task is resolved in a scope of its own, so it acquires (and
        finalizes) its own db session and every other request-scoped resource
        instead of borrowing the caller's — which is closed as soon as the
        caller returns. ``params`` carries the data of this particular run and
        is available in that scope under its own type.
        """
        raise NotImplementedError
