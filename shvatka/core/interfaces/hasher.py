import typing


class PasswordHasher(typing.Protocol):
    async def hash(self, password: str) -> str:
        raise NotImplementedError

    async def verify(self, plain_password: str, hashed_password: str) -> bool:
        raise NotImplementedError
