import typing


class PasswordHasher(typing.Protocol):
    """Hashing a password is deliberately slow — that is what makes it worth
    anything — so both methods are async: an implementation is expected to do
    the work somewhere other than the event loop.
    """

    async def hash(self, password: str) -> str:
        raise NotImplementedError

    async def verify(self, plain_password: str, hashed_password: str) -> bool:
        raise NotImplementedError
