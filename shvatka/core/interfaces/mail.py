import typing


class EmailSender(typing.Protocol):
    async def send_confirmation_code(self, email: str, code: str) -> None:
        """Send an email containing the confirmation code to the given address."""
        ...
