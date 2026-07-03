import typing


class OneTimeTokenCreator(typing.Protocol):
    async def save_new_token(self, *, token_len: int = ..., expire: int = ..., **dct: dict) -> str:
        raise NotImplementedError
