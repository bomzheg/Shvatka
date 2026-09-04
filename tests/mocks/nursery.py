from typing import Any

from shvatka.core.interfaces.nursery import BackgroundTask, Nursery


class FakeNursery(Nursery):
    def __init__(self) -> None:
        self.spawned: list[tuple[BackgroundTask, dict[str, Any]]] = []

    def spawn(self, task: BackgroundTask, /, *args: Any, **kwargs: Any) -> None:
        self.spawned.append((task, kwargs))
