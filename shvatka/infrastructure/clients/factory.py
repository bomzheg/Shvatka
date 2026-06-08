from shvatka.common.config.models.main import FileStorageConfig
from shvatka.infrastructure.clients.file_storage import LocalFileStorage


def create_file_storage(config: FileStorageConfig) -> LocalFileStorage:
    return LocalFileStorage(config)
