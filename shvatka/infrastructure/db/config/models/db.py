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
    """connections kept open. one process serves the api, every telegram update
    and every background job, and each of them holds one for the length of its
    own scope — so this is the ceiling on how many of them can run at once"""

    max_overflow: int = 10
    """extra connections opened past ``pool_size`` under load and closed again
    afterwards. exhausting both is what makes a trivial request wait"""

    pool_timeout: float = 30.0
    """how long a caller waits for a free connection before giving up with
    ``sqlalchemy.exc.TimeoutError``"""

    pool_recycle: int = 1800
    """drop a connection older than this, in seconds, rather than hand out one
    the database or a proxy has already closed. ``-1`` to never recycle"""

    pool_pre_ping: bool = False
    """check a connection is alive before handing it out. a round trip per
    checkout — worth it across a flaky link, not against a local database"""

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
