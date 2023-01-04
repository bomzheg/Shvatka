from typing import BinaryIO

from shvatka.interfaces.clients.file_storage import FileStorage
from shvatka.models.dto import scn
from shvatka.models.dto.scn import FileContentLink


class MemoryFileStorage(FileStorage):
    def __init__(self):
        self.storage = {}

    async def put_content(self, local_file_name: str, content: BinaryIO) -> FileContentLink:
        self.storage[local_file_name] = content
        return FileContentLink(file_path=local_file_name)

    async def put(self, file_meta: scn.UploadedFileMeta, content: BinaryIO) -> scn.FileMeta:
        return scn.FileMeta(
            file_content_link=await self.put_content(file_meta.local_file_name, content),
            guid=file_meta.guid,
            original_filename=file_meta.original_filename,
            extension=file_meta.extension,
            tg_link=file_meta.tg_link,
        )

    async def get(self, file_link: FileContentLink) -> BinaryIO:
        return self.storage[file_link.file_path]
