from dataclass_factory import Factory

from src.common.config.models.main import Config, FileStorageConfig
from src.common.config.models.paths import Paths
from src.infrastructure.db.config.parser.db import load_db_config, load_redis_config


def load_config(config_dct: dict, paths: Paths, dcf: Factory) -> Config:
    return Config(
        paths=paths,
        db=load_db_config(config_dct["db"]),
        redis=load_redis_config(config_dct["redis"]),
        file_storage_config=load_file_storage_config(config_dct["file-storage-config"], dcf),
    )


def load_file_storage_config(config_dct: dict, dcf: Factory) -> FileStorageConfig:
    return dcf.load(config_dct, FileStorageConfig)
