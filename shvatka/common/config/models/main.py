from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from shvatka.infrastructure.db.config.models.db import DBConfigProperties, RedisConfig


@dataclass
class AppConfig:
    name: str


@dataclass
class FileStorageConfig:
    path: Path
    mkdir: bool
    parents: bool
    exist_ok: bool


@dataclass
class WebConfig:
    base_url: str


@dataclass
class MailConfig:
    enabled: bool = False
    host: str = ""
    port: int = 587
    username: str = ""
    password: str = ""
    from_addr: str = ""
    use_tls: bool = False
    start_tls: bool = True


@dataclass(kw_only=True)
class Config:
    """The shared part of config.yml — one field per top level section of it.

    ``Paths`` is deliberately not a field here: it is the input that locates
    config.yml, so it can't be read out of it. Take it from DI instead.
    """

    app: AppConfig
    db: DBConfigProperties
    redis: RedisConfig
    file_storage_config: FileStorageConfig
    web: WebConfig
    mail: MailConfig = field(default_factory=MailConfig)
    features: FeaturesConfig
    superusers: list[int] = field(default_factory=list)
    """tg ids of users allowed to use the admin panel / superuser bot commands"""


@dataclass(kw_only=True)
class FeaturesConfig:
    level_test: bool
    merge_team_button: bool
