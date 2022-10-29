from dataclasses import dataclass
from datetime import timedelta


@dataclass
class AuthConfig:
    secret_key: str
    token_expire: timedelta
