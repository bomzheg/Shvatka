from __future__ import annotations
from dataclasses import dataclass

import logging
from enum import Enum

from aiogram.dispatcher.fsm.storage.base import BaseStorage
from aiogram.dispatcher.fsm.storage.memory import MemoryStorage
from aiogram.dispatcher.fsm.storage.redis import RedisStorage
from redis.asyncio.client import Redis

logger = logging.getLogger(__name__)


@dataclass
class DBConfig:
    type: str = None
    connector: str = None
    host: str = None
    port: int = None
    login: str = None
    password: str = None
    name: str = None
    path: str = None

    @property
    def uri(self):
        if self.type in ('mysql', 'postgresql'):
            url = (
                f'{self.type}+{self.connector}://'
                f'{self.login}:{self.password}'
                f'@{self.host}:{self.port}/{self.name}'
            )
        elif self.type == 'sqlite':
            url = (
                f'{self.type}://{self.path}'
            )
        else:
            raise ValueError("DB_TYPE not mysql, sqlite or postgres")
        logger.debug(url)
        return url


class StorageType(Enum):
    memory = "memory"
    redis = "redis"


@dataclass
class StorageConfig:
    type_: StorageType
    redis: RedisConfig | None = None

    def create_storage(self) -> BaseStorage:
        logger.info("creating storage for type %s", self.type_)
        match self.type_:
            case StorageType.memory:
                return MemoryStorage()
            case StorageType.redis:
                return RedisStorage(self.redis.create_redis())
            case _:
                raise NotImplementedError


@dataclass
class RedisConfig:
    url: str
    port: int = 6379
    db: int = 1

    def create_redis(self) -> Redis:
        logger.info("created storage for %s", self)
        return Redis(host=self.url, port=self.port, db=self.db)

