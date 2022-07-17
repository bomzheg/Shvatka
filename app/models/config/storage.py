from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

from aiogram.dispatcher.fsm.storage.base import BaseStorage
from aiogram.dispatcher.fsm.storage.memory import MemoryStorage
from aiogram.dispatcher.fsm.storage.redis import RedisStorage

from app.models.config.db import RedisConfig

logger = logging.getLogger(__name__)


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
