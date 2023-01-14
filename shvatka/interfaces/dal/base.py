from typing import Protocol


class Committer(Protocol):
    async def commit(self) -> None:
        raise NotImplementedError
