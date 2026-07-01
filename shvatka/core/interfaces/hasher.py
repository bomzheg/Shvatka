import typing


class PasswordHasher(typing.Protocol):
    def hash(self, password: str) -> str:
        ...

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        ...
