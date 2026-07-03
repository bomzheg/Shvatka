import typing


class OneTimeTokenCreator(typing.Protocol):
    async def save_new_token(self, **dct: dict) -> str:
        raise NotImplementedError
