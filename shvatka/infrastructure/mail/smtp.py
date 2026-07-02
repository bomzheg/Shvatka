import logging
from email.message import EmailMessage

import aiosmtplib

from shvatka.common.config.models.main import MailConfig

logger = logging.getLogger(__name__)


class SmtpEmailSender:
    def __init__(self, config: MailConfig) -> None:
        self.config = config

    async def send_confirmation_code(self, email: str, code: str) -> None:
        message = EmailMessage()
        message["From"] = self.config.from_addr or self.config.username
        message["To"] = email
        message["Subject"] = "Shvatka: код подтверждения"
        message.set_content(
            f"Ваш код подтверждения электронной почты: {code}\n\n"
            "Если вы не запрашивали его, просто проигнорируйте это письмо."
        )
        await aiosmtplib.send(
            message,
            hostname=self.config.host,
            port=self.config.port,
            username=self.config.username or None,
            password=self.config.password or None,
            use_tls=self.config.use_tls,
            start_tls=self.config.start_tls if not self.config.use_tls else False,
        )
        logger.info("confirmation email sent to %s", email)
