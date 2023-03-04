from shvatka.common.config.models.main import FileStorageConfig
from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.infrastructure.clients.file_storage import LocalFileStorage


def create_file_storage(config: FileStorageConfig) -> FileStorage:
    return LocalFileStorage(config)
