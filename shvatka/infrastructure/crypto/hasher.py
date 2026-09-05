import asyncio

from passlib.context import CryptContext


class BcryptPasswordHasher:
    def __init__(self) -> None:
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def hash(self, password: str) -> str:
        return await asyncio.to_thread(self.pwd_context.hash, password)

    async def verify(self, plain_password: str, hashed_password: str) -> bool:
        return await asyncio.to_thread(self.pwd_context.verify, plain_password, hashed_password)
