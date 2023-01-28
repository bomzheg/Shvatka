from common.config.models.main import FileStorageConfig
from infrastructure.clients.file_storage import LocalFileStorage
from shvatka.interfaces.clients.file_storage import FileStorage


def create_file_storage(config: FileStorageConfig) -> FileStorage:
    return LocalFileStorage(config)
