import logging
from io import BytesIO
from typing import BinaryIO

from common.config.models.main import FileStorageConfig
from shvatka.interfaces.clients.file_storage import FileStorage
from shvatka.models.dto.scn import FileContentLink

logger = logging.getLogger(__name__)


class LocalFileStorage(FileStorage):
    def __init__(self, config: FileStorageConfig):
        self.path = config.path
        logger.info("as local file storage use '%s'", self.path)
        if config.mkdir:
            self.path.mkdir(exist_ok=config.exist_ok, parents=config.parents)

    async def put(self, local_file_name: str, content: BinaryIO) -> FileContentLink:
        result_path = self.path / local_file_name
        with result_path.open("wb") as f:
            f.write(content.read())
        return FileContentLink(file_path=str(result_path))

    async def get(self, file_link: FileContentLink) -> BinaryIO:
        with open(file_link.file_path, "rb") as f:
            result = BytesIO(f.read())
        return result
