from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from shvatka.infrastructure.db.config.models.db import DBConfig, RedisConfig
from .paths import Paths


@dataclass
class Config:
    app: AppConfig
    paths: Paths
    db: DBConfig
    redis: RedisConfig
    file_storage_config: FileStorageConfig
    web: WebConfig
    mail: MailConfig
    superusers: list[int]
    """tg ids of users allowed to use the admin panel / superuser bot commands"""

    @property
    def app_dir(self) -> Path:
        return self.paths.app_dir

    @property
    def config_path(self) -> Path:
        return self.paths.config_path

    @property
    def log_path(self) -> Path:
        return self.paths.log_path


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
