import logging

logger = logging.getLogger(__name__)


class ConsoleEmailSender:
    async def send_confirmation_code(self, email: str, code: str) -> None:
        logger.warning(
            "email sending is not configured, confirmation code for %s is %s", email, code
        )

    async def send_one_time_link(self, email: str, url: str) -> None:
        logger.warning(
            "email sending is not configured, one time login link for %s is %s", email, url
        )
