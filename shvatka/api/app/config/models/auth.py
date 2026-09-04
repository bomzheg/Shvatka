from dataclasses import dataclass
from datetime import timedelta
from typing import Literal


@dataclass
class AuthConfig:
    secret_key: str
    token_expire: timedelta
    bot_username: str
    samesite: Literal["lax", "strict", "none"] | None
    httponly: bool
    secure: bool
    auth_url: str
    bot_token: str
    # Empty (the default) means a host-only cookie: the browser sends it back
    # only to the host that set it. Naming a parent domain here shares the
    # cookie with every deployment under it — and since the cookie is keyed by
    # (name, domain, path), the next deployment to log a user in overwrites the
    # previous one's token. Set it only for a deployment that really spans
    # subdomains, and then give that deployment its own `cookie_name`.
    domain: str | None = None
    cookie_name: str = "Authorization"
    disable_cors: bool = False
    enable_basic: bool = False

    @property
    def cookie_domain(self) -> str | None:
        return self.domain or None
