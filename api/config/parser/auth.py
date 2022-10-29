from datetime import timedelta

from api.config.models.auth import AuthConfig


def load_auth(dct: dict) -> AuthConfig:
    return AuthConfig(
        secret_key=dct["secret-key"],
        token_expire=timedelta(minutes=dct["token-expire-minutes"]),
    )
