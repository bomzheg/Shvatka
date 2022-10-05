from typing import Protocol


class Reader(Protocol):
    pass


class Writer(Protocol):
    pass


class Committer(Writer):
    async def commit(self) -> None:
        raise NotImplementedError
