from __future__ import annotations

from dataclasses import dataclass, field

from shvatka.api.app.config.models.auth import AuthConfig
from shvatka.api.app.config.models.push import PushConfig
from shvatka.common.config.models.main import Config


@dataclass(kw_only=True)
class ApiSection:
    """The api section of config.yml."""

    auth: AuthConfig
    push: PushConfig = field(default_factory=PushConfig)
    context_path: str = ""
    enable_logging: bool = False


@dataclass(kw_only=True)
class ApiConfig(Config):
    api: ApiSection
