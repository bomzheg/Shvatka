from typing import BinaryIO

from src.shvatka.interfaces.clients.file_storage import FileStorage
from src.shvatka.models.dto import scn


class MemoryFileStorage(FileStorage):
    def __init__(self):
        self.storage = {}

    async def put_content(self, local_file_name: str, content: BinaryIO) -> scn.FileContentLink:
        self.storage[local_file_name] = content
        return scn.FileContentLink(file_path=local_file_name)

    async def put(self, file_meta: scn.UploadedFileMeta, content: BinaryIO) -> scn.FileMeta:
        return scn.FileMeta(
            file_content_link=await self.put_content(file_meta.local_file_name, content),
            guid=file_meta.guid,
            original_filename=file_meta.original_filename,
            extension=file_meta.extension,
            tg_link=file_meta.tg_link,
        )

    async def get(self, file_link: scn.FileContentLink) -> BinaryIO:
        return self.storage[file_link.file_path]
