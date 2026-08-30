from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from shvatka.common.config.models.monitoring import MonitoringConfig
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
class DocsConfig:
    base_url: str = "https://bomzheg.github.io/Shvatka"
    component: str = "shvatka"
    version: str = ""


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
    app: AppConfig
    db: DBConfigProperties
    redis: RedisConfig
    file_storage_config: FileStorageConfig
    web: WebConfig
    docs: DocsConfig = field(default_factory=DocsConfig)
    mail: MailConfig = field(default_factory=MailConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    features: FeaturesConfig
    superusers: list[int] = field(default_factory=list)
    """tg ids of users allowed to use the admin panel / superuser bot commands"""


@dataclass(kw_only=True)
class FeaturesConfig:
    level_test: bool
    merge_team_button: bool
    tg_channel_publication: bool
    forum_publication: bool
