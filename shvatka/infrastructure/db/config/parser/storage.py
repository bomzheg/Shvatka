import dature

from shvatka.common.config.models.paths import Paths
from shvatka.common.config.parser.config_source import config_source
from shvatka.infrastructure.db.config.models.storage import StorageConfig


def load_storage_config(paths: Paths) -> StorageConfig:
    return dature.load(config_source(paths, prefix="storage"), schema=StorageConfig)
