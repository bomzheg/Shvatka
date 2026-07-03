from dishka import Provider, Scope, provide

from shvatka.common import Config
from shvatka.core.interfaces.hasher import PasswordHasher
from shvatka.core.interfaces.mail import EmailSender
from shvatka.core.services.email import (
    EmailRegisterInteractor,
    EmailLinkInteractor,
    EmailConfirmInteractor,
    EmailResendInteractor,
    ForgotPasswordInteractor,
)
from shvatka.infrastructure.crypto.hasher import BcryptPasswordHasher
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.mail import create_email_sender


class MailProvider(Provider):
    scope = Scope.APP

    @provide
    def get_email_sender(self, config: Config) -> EmailSender:
        return create_email_sender(config.mail)

    @provide
    def get_password_hasher(self) -> PasswordHasher:
        return BcryptPasswordHasher()


class EmailInteractorProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def register(
        self, dao: HolderDao, hasher: PasswordHasher, sender: EmailSender
    ) -> EmailRegisterInteractor:
        return EmailRegisterInteractor(
            dao=dao.email,
            player_dao=dao.player,
            hasher=hasher,
            store=dao.email_confirm,
            sender=sender,
        )

    @provide
    def link(self, dao: HolderDao, sender: EmailSender) -> EmailLinkInteractor:
        return EmailLinkInteractor(dao=dao.email, store=dao.email_confirm, sender=sender)

    @provide
    def confirm(self, dao: HolderDao) -> EmailConfirmInteractor:
        return EmailConfirmInteractor(dao=dao.email, store=dao.email_confirm)

    @provide
    def resend(self, dao: HolderDao, sender: EmailSender) -> EmailResendInteractor:
        return EmailResendInteractor(dao=dao.email, store=dao.email_confirm, sender=sender)

    @provide
    def forgot_password(
        self, dao: HolderDao, sender: EmailSender, config: Config
    ) -> ForgotPasswordInteractor:
        return ForgotPasswordInteractor(
            dao=dao.email,
            limiter=dao.rate_limiter,
            token_creator=dao.one_time_token,
            sender=sender,
            base_url=config.web.base_url,
        )
