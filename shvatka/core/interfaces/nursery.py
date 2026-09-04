from collections.abc import Awaitable, Callable
from typing import Any, Protocol

BackgroundTask = Callable[..., Awaitable[None]]


class Nursery(Protocol):
    def spawn(self, task: BackgroundTask, /, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError
