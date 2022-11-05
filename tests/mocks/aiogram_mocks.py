import typing

T = typing.TypeVar("T")


async def mock_coro(value: T) -> T:
    return value
