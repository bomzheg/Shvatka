from datetime import timedelta

from shvatka.api.config.models.auth import AuthConfig


def load_auth(dct: dict) -> AuthConfig:
    return AuthConfig(
        secret_key=dct["secret-key"],
        token_expire=timedelta(minutes=dct["token-expire-minutes"]),
        bot_token=dct["bot-token"],
        bot_username=dct["bot-username"],
        auth_url=dct["auth-url"],
        domain=dct["domain"],
        samesite=dct["samesite"],
        secure=bool(dct["secure"]),
        httponly=bool(dct["httponly"]),
    )
