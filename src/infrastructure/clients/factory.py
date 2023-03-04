from src.common.config.models.main import FileStorageConfig
from src.infrastructure.clients.file_storage import LocalFileStorage
from src.shvatka.interfaces.clients.file_storage import FileStorage


def create_file_storage(config: FileStorageConfig) -> FileStorage:
    return LocalFileStorage(config)
