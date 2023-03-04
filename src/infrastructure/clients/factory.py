from src.common.config.models.main import FileStorageConfig
from src.core.interfaces.clients.file_storage import FileStorage
from src.infrastructure.clients.file_storage import LocalFileStorage


def create_file_storage(config: FileStorageConfig) -> FileStorage:
    return LocalFileStorage(config)
