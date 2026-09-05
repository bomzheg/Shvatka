from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger(__name__)


class DBConfig(Protocol):
    echo: bool
    pool_size: int
    max_overflow: int
    pool_timeout: float
    pool_recycle: int
    pool_pre_ping: bool

    @property
    def uri(self):
        raise NotImplementedError


@dataclass
class DBConfigProperties(DBConfig):
    type: str | None = None
    connector: str | None = None
    host: str | None = None
    port: int | None = None
    login: str | None = None
    password: str | None = None
    name: str | None = None
    path: str | None = None
    echo: bool = False

    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: float = 30.0
    pool_recycle: int = 1800
    pool_pre_ping: bool = False

    @property
    def uri(self):
        if self.type in ("mysql", "postgresql"):
            url = (
                f"{self.type}+{self.connector}://"
                f"{self.login}:{self.password}"
                f"@{self.host}:{self.port}/{self.name}"
            )
        elif self.type == "sqlite":
            url = f"{self.type}://{self.path}"
        else:
            raise ValueError("DB_TYPE not mysql, sqlite or postgres")
        logger.debug(url)
        return url


@dataclass
class RedisConfig:
    url: str
    port: int = 6379
    db: int = 1
