from dataclasses import dataclass
from datetime import timedelta
from typing import Literal


@dataclass
class AuthConfig:
    secret_key: str
    token_expire: timedelta
    bot_username: str
    domain: str
    samesite: Literal["lax", "strict", "none"] | None
    httponly: bool
    secure: bool
    auth_url: str
    bot_token: str
