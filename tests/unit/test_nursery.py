import asyncio
from dataclasses import dataclass, field
from collections.abc import AsyncIterable

import pytest
from dishka import FromDishka, Provider, Scope, from_context, make_async_container, provide

from shvatka.infrastructure.nursery import AsyncioNursery


@dataclass
class Journal:
    """What the spawned tasks did, in order."""

    events: list[str] = field(default_factory=list)
    done: asyncio.Event = field(default_factory=asyncio.Event)


class Resource:
    """Stands for a db session: acquired and finalized by the task's own scope."""

    def __init__(self, journal: Journal) -> None:
        self.journal = journal


async def greet(name: str, resource: FromDishka[Resource]) -> None:
    resource.journal.events.append(f"hello {name}")
    resource.journal.done.set()


async def fail(name: str, resource: FromDishka[Resource]) -> None:
    resource.journal.done.set()
    raise ValueError("task failed")


async def forever(resource: FromDishka[Resource]) -> None:
    resource.journal.done.set()
    await asyncio.Event().wait()


class TasksProvider(Provider):
    journal = from_context(Journal, scope=Scope.APP)

    @provide(scope=Scope.REQUEST)
    async def get_resource(self, journal: Journal) -> AsyncIterable[Resource]:
        journal.events.append("resource acquired")
        yield Resource(journal)
        journal.events.append("resource released")


@pytest.fixture
def journal() -> Journal:
    return Journal()


@pytest.mark.asyncio
async def test_spawned_task_runs_in_its_own_scope(journal: Journal):
    container = make_async_container(TasksProvider(), context={Journal: journal})
    nursery = AsyncioNursery(container)

    nursery.spawn(greet, name="Harry")
    await asyncio.wait_for(journal.done.wait(), timeout=1)
    await nursery.close()

    assert journal.events == ["resource acquired", "hello Harry", "resource released"]
    await container.close()


@pytest.mark.asyncio
async def test_positional_arguments_are_passed_through(journal: Journal):
    container = make_async_container(TasksProvider(), context={Journal: journal})
    nursery = AsyncioNursery(container)

    nursery.spawn(greet, "Hermione")
    await asyncio.wait_for(journal.done.wait(), timeout=1)
    await nursery.close()

    assert "hello Hermione" in journal.events
    await container.close()


@pytest.mark.asyncio
async def test_failed_task_is_contained_and_finalized(journal: Journal):
    container = make_async_container(TasksProvider(), context={Journal: journal})
    nursery = AsyncioNursery(container)

    nursery.spawn(fail, name="Harry")
    await asyncio.wait_for(journal.done.wait(), timeout=1)
    await nursery.close()

    # the failure is swallowed (and logged), the task's resources are released
    assert journal.events == ["resource acquired", "resource released"]
    await container.close()


@pytest.mark.asyncio
async def test_one_failure_does_not_cancel_its_siblings(journal: Journal):
    container = make_async_container(TasksProvider(), context={Journal: journal})
    nursery = AsyncioNursery(container)

    nursery.spawn(fail, name="Harry")
    nursery.spawn(greet, name="Hermione")
    await asyncio.wait_for(journal.done.wait(), timeout=1)
    await asyncio.sleep(0)
    await nursery.close()

    assert "hello Hermione" in journal.events
    await container.close()


@pytest.mark.asyncio
async def test_close_cancels_unfinished_tasks(journal: Journal):
    container = make_async_container(TasksProvider(), context={Journal: journal})
    nursery = AsyncioNursery(container)

    nursery.spawn(forever)
    await asyncio.wait_for(journal.done.wait(), timeout=1)
    await nursery.close()

    assert journal.events == ["resource acquired", "resource released"]
    await container.close()
