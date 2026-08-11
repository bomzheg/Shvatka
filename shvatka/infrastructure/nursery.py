import asyncio
import logging
from typing import Any, AsyncIterable

from dishka import AsyncContainer, Provider, Scope, provide
from dishka.integrations.base import wrap_injection

from shvatka.core.interfaces.nursery import BackgroundTask, Nursery

logger = logging.getLogger(__name__)


class AsyncioNursery(Nursery):
    """The one place in the app allowed to start a detached asyncio task.

    Keeping ``create_task`` here is what makes such a task supervised: a strong
    reference is held until it finishes (so the loop can't garbage collect it
    mid-flight), a failure is logged instead of disappearing into a
    never-awaited task, and whatever is still running on shutdown is cancelled
    and awaited.
    """

    def __init__(self, container: AsyncContainer) -> None:
        self.container = container
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
            logger.error("background task %s failed", task.__name__, exc_info=e)

    async def close(self) -> None:
        if not self.tasks:
            return
        # detached work can be minutes long (publishing a scenario), so
        # shutdown cancels it rather than waiting it out
        logger.info("cancelling %s unfinished background tasks", len(self.tasks))
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)


class NurseryProvider(Provider):
    scope = Scope.APP

    @provide
    async def get_nursery(self, container: AsyncContainer) -> AsyncIterable[Nursery]:
        nursery = AsyncioNursery(container)
        yield nursery
        await nursery.close()
