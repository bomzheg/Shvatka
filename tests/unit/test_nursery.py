import asyncio
from dataclasses import dataclass, field
from typing import AsyncIterable

import pytest
from dishka import Provider, Scope, from_context, make_async_container, provide

from shvatka.infrastructure.nursery import AsyncioNursery


@dataclass
class Journal:
    """What the spawned tasks did, in order."""

    events: list[str] = field(default_factory=list)
    done: asyncio.Event = field(default_factory=asyncio.Event)


@dataclass(kw_only=True, slots=True, frozen=True)
class GreetParams:
    name: str


class Resource:
    """Stands for a db session: acquired and finalized by the task's own scope."""

    def __init__(self, journal: Journal) -> None:
        self.journal = journal
        self.closed = False


@dataclass(kw_only=True, slots=True, frozen=True)
class GreetTask:
    params: GreetParams
    resource: Resource

    async def __call__(self) -> None:
        self.resource.journal.events.append(f"hello {self.params.name}")
        self.resource.journal.done.set()


@dataclass(kw_only=True, slots=True, frozen=True)
class FailingTask:
    params: GreetParams
    resource: Resource

    async def __call__(self) -> None:
        self.resource.journal.done.set()
        raise ValueError("task failed")


@dataclass(kw_only=True, slots=True, frozen=True)
class ForeverTask:
    params: GreetParams
    resource: Resource

    async def __call__(self) -> None:
        self.resource.journal.done.set()
        await asyncio.Event().wait()


class TasksProvider(Provider):
    journal = from_context(Journal, scope=Scope.APP)
    params = from_context(GreetParams, scope=Scope.REQUEST)
    greet = provide(GreetTask, scope=Scope.REQUEST)
    failing = provide(FailingTask, scope=Scope.REQUEST)
    forever = provide(ForeverTask, scope=Scope.REQUEST)

    @provide(scope=Scope.REQUEST)
    async def get_resource(self, journal: Journal) -> AsyncIterable[Resource]:
        resource = Resource(journal)
        journal.events.append("resource acquired")
        yield resource
        resource.closed = True
        journal.events.append("resource released")


@pytest.fixture
def journal() -> Journal:
    return Journal()


@pytest.mark.asyncio
async def test_spawned_task_runs_in_its_own_scope(journal: Journal):
    container = make_async_container(TasksProvider(), context={Journal: journal})
    nursery = AsyncioNursery(container)

    nursery.spawn(GreetTask, GreetParams(name="Harry"))
    await asyncio.wait_for(journal.done.wait(), timeout=1)
    await nursery.close()

    assert journal.events == ["resource acquired", "hello Harry", "resource released"]
    await container.close()


@pytest.mark.asyncio
async def test_failed_task_is_contained_and_finalized(journal: Journal):
    container = make_async_container(TasksProvider(), context={Journal: journal})
    nursery = AsyncioNursery(container)

    nursery.spawn(FailingTask, GreetParams(name="Harry"))
    await asyncio.wait_for(journal.done.wait(), timeout=1)
    await nursery.close()

    # the failure is swallowed (and logged), the task's resources are released
    assert journal.events == ["resource acquired", "resource released"]
    await container.close()


@pytest.mark.asyncio
async def test_close_cancels_unfinished_tasks(journal: Journal):
    container = make_async_container(TasksProvider(), context={Journal: journal})
    nursery = AsyncioNursery(container)

    nursery.spawn(ForeverTask, GreetParams(name="Harry"))
    await asyncio.wait_for(journal.done.wait(), timeout=1)
    await nursery.close()

    assert journal.events == ["resource acquired", "resource released"]
    await container.close()
