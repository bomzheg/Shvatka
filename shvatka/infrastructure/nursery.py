import asyncio
import logging
import typing
from typing import Any
from collections.abc import AsyncIterable

from dishka import AsyncContainer, Provider, Scope, provide
from dishka.integrations.base import wrap_injection

from shvatka.core.interfaces.nursery import BackgroundTask, Nursery

logger = logging.getLogger(__name__)

DEFAULT_DRAIN_TIMEOUT: typing.Final = 15.0


class AsyncioNursery(Nursery):
    """The one place in the app allowed to start a detached asyncio task.

    Keeping ``create_task`` here is what makes such a task supervised: a strong
    reference is held until it finishes (so the loop can't garbage collect it
    mid-flight), a failure is logged instead of disappearing into a
    never-awaited task, and whatever is still running on shutdown is given a
    moment to finish before it is cancelled and awaited.
    """

    def __init__(
        self, container: AsyncContainer, drain_timeout: float = DEFAULT_DRAIN_TIMEOUT
    ) -> None:
        self.container = container
        self.drain_timeout = drain_timeout
        self.tasks: set[asyncio.Task[None]] = set()

    def spawn(self, task: BackgroundTask, /, *args: Any, **kwargs: Any) -> None:
        spawned = asyncio.create_task(  # noqa: TID251  # the nursery is the exception
            self._run(task, *args, **kwargs), name=task.__name__
        )
        self.tasks.add(spawned)
        spawned.add_done_callback(self.tasks.discard)

    async def _run(self, task: BackgroundTask, /, *args: Any, **kwargs: Any) -> None:
        try:
            async with self.container() as container:
                injected = wrap_injection(
                    func=task,
                    remove_depends=True,
                    container_getter=lambda _, __: container,
                    is_async=True,
                )
                await injected(*args, **kwargs)
        except asyncio.CancelledError:
            logger.info("background task %s cancelled", task.__name__)
            raise
        except Exception as e:
            logger.exception("background task %s failed", task.__name__, exc_info=e)

    async def close(self) -> None:
        """Wait a bounded time for running tasks, then cancel the rest.

        Nothing will re-run a cancelled job, so a team would be left with half a
        puzzle. Bounded because some jobs (publishing a scenario) take minutes.
        """
        if not self.tasks:
            return
        logger.info(
            "draining %s unfinished background tasks, up to %s seconds",
            len(self.tasks),
            self.drain_timeout,
        )
        await asyncio.wait(set(self.tasks), timeout=self.drain_timeout)
        # re-read: anything spawned during the drain is nobody's to wait for
        leftover = set(self.tasks)
        if not leftover:
            logger.info("all background tasks finished before shutdown")
            return
        logger.warning("cancelling %s background tasks that outlived the drain", len(leftover))
        for task in leftover:
            task.cancel()
        await asyncio.gather(*leftover, return_exceptions=True)


class NurseryProvider(Provider):
    scope = Scope.APP

    @provide
    async def get_nursery(self, container: AsyncContainer) -> AsyncIterable[Nursery]:
        nursery = AsyncioNursery(container)
        yield nursery
        await nursery.close()
