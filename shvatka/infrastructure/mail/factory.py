from shvatka.common.config.models.main import MailConfig
from shvatka.core.interfaces.mail import EmailSender
from .console import ConsoleEmailSender
from .smtp import SmtpEmailSender


def create_email_sender(config: MailConfig) -> EmailSender:
    if config.enabled and config.host:
        return SmtpEmailSender(config)
    return ConsoleEmailSender()
