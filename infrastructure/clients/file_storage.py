import logging
from io import BytesIO
from typing import BinaryIO

from common.config.models.main import FileStorageConfig
from shvatka.interfaces.clients.file_storage import FileStorage
from shvatka.models.dto import scn

logger = logging.getLogger(
    __name__)


# TODO split it to file_storage and proxy that upload to tg and file storage
class LocalFileStorage(FileStorage):
    def __init__(self, config: FileStorageConfig):
        self.path = config.path
        logger.info("as local file storage use '%s'", self.path)
        if config.mkdir:
            self.path.mkdir(exist_ok=config.exist_ok, parents=config.parents)

    async def put(self, file_meta: scn.UploadedFileMeta, content: BinaryIO) -> scn.FileMeta:
        if not file_meta.tg_link:
            pass  # TODO upload to telegram
        return scn.FileMeta(
            file_content_link=await self.put_content(file_meta.local_file_name, content),
            guid=file_meta.guid,
            original_filename=file_meta.original_filename,
            extension=file_meta.extension,
            tg_link=file_meta.tg_link,
        )

    async def put_content(self, local_file_name: str, content: BinaryIO) -> scn.FileContentLink:
        result_path = self.path / local_file_name
        with result_path.open("wb") as f:
            f.write(content.read())
        return scn.FileContentLink(file_path=str(result_path))

    async def get(self, file_link: scn.FileContentLink) -> BinaryIO:
        with open(file_link.file_path, "rb") as f:
            result = BytesIO(f.read())
        return result
