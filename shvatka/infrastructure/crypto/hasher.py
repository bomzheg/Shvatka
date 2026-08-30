import asyncio

from passlib.context import CryptContext


class BcryptPasswordHasher:
    """Bcrypt, in a thread.

    A bcrypt round is hundreds of milliseconds of cpu by design. On the event
    loop that is hundreds of milliseconds nothing else in the process moves —
    and it is not only the login endpoint that pays it: any request whose token
    is missing or invalid falls through to basic auth, which verifies a
    password. Bcrypt is native code that releases the gil, so a thread really
    does run it beside the loop rather than merely interleaved with it.
    """

    def __init__(self) -> None:
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def hash(self, password: str) -> str:
        return await asyncio.to_thread(self.pwd_context.hash, password)

    async def verify(self, plain_password: str, hashed_password: str) -> bool:
        return await asyncio.to_thread(self.pwd_context.verify, plain_password, hashed_password)
