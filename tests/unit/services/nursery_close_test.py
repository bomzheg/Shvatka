import asyncio
import time

import pytest

from shvatka.infrastructure.nursery import AsyncioNursery


class FakeContainer:
    """Enough of a dishka container for a task with no injected parameters."""

    def __call__(self) -> "FakeContainer":
        return self

    async def __aenter__(self) -> "FakeContainer":
        return self

    async def __aexit__(self, *args: object) -> bool:
        return False


def build_nursery(drain_timeout: float) -> AsyncioNursery:
    return AsyncioNursery(FakeContainer(), drain_timeout=drain_timeout)


@pytest.mark.asyncio
async def test_short_task_is_allowed_to_finish() -> None:
    finished = asyncio.Event()

    async def deliver() -> None:
        await asyncio.sleep(0.01)
        finished.set()

    nursery = build_nursery(drain_timeout=1)
    nursery.spawn(deliver)

    await nursery.close()

    assert finished.is_set(), "a puzzle being sent must not be cut in half by a restart"
    assert not nursery.tasks


@pytest.mark.asyncio
async def test_long_task_is_cancelled_once_the_drain_is_over() -> None:
    finished = asyncio.Event()
    cancelled = asyncio.Event()

    async def publish_scenario() -> None:
        try:
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            cancelled.set()
            raise
        finished.set()

    nursery = build_nursery(drain_timeout=0.05)
    nursery.spawn(publish_scenario)

    started = time.monotonic()
    await nursery.close()
    spent = time.monotonic() - started

    assert cancelled.is_set()
    assert not finished.is_set()
    assert spent < 5


@pytest.mark.asyncio
async def test_closing_with_nothing_running_is_free() -> None:
    await build_nursery(drain_timeout=30).close()
