import typing


class EmailSender(typing.Protocol):
    async def send_confirmation_code(self, email: str, code: str) -> None:
        """Send an email containing the confirmation code to the given address."""
        raise NotImplementedError

    async def send_one_time_link(self, email: str, url: str) -> None:
        """Send an email containing a one-time login link to the given address."""
        raise NotImplementedError
