from typing import Any

from shvatka.config.db import load_redis_config
from shvatka.models.config.storage import StorageConfig, StorageType


def load_storage_config(dct: dict[str, Any]) -> StorageConfig:
    config = StorageConfig(type_=StorageType[dct["type"]])
    if config.type_ == StorageType.redis:
        config.redis = load_redis_config(dct["redis"])
    return config
