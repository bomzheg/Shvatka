from dataclasses import dataclass
from datetime import timedelta


@dataclass
class AuthConfig:
    secret_key: str
    token_expire: timedelta
    bot_username: str
    auth_url: str
    bot_token: str
