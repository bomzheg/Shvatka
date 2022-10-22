from typing import Any

from db.config.models.storage import StorageConfig, StorageType
from db.config.parser.db import load_redis_config


def load_storage_config(dct: dict[str, Any]) -> StorageConfig:
    config = StorageConfig(type_=StorageType[dct["type"]])
    if config.type_ == StorageType.redis:
        config.redis = load_redis_config(dct["redis"])
    return config
