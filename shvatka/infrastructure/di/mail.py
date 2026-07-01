from dishka import Provider, Scope, provide

from shvatka.common import Config
from shvatka.core.interfaces.hasher import PasswordHasher
from shvatka.core.interfaces.mail import EmailSender
from shvatka.infrastructure.crypto.hasher import BcryptPasswordHasher
from shvatka.infrastructure.mail import create_email_sender


class MailProvider(Provider):
    scope = Scope.APP

    @provide
    def get_email_sender(self, config: Config) -> EmailSender:
        return create_email_sender(config.mail)

    @provide
    def get_password_hasher(self) -> PasswordHasher:
        return BcryptPasswordHasher()
