import typing


class EmailSender(typing.Protocol):
    async def send_confirmation_code(self, email: str, code: str) -> None:
        raise NotImplementedError

    async def send_one_time_link(self, email: str, url: str) -> None:
        raise NotImplementedError
