import logging

logger = logging.getLogger(__name__)


class ConsoleEmailSender:
    """Fallback email sender that only logs the message.

    Used when no SMTP relay is configured, so that local development and
    tests work without real credentials.
    """

    async def send_confirmation_code(self, email: str, code: str) -> None:
        logger.warning(
            "email sending is not configured, confirmation code for %s is %s", email, code
        )

    async def send_one_time_link(self, email: str, url: str) -> None:
        logger.warning(
            "email sending is not configured, one time login link for %s is %s", email, url
        )
