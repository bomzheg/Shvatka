from typing import BinaryIO

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.models.dto import hints


class MemoryFileStorage(FileStorage):
    def __init__(self) -> None:
        self.storage: dict[str, BinaryIO] = {}

    async def put_content(self, local_file_name: str, content: BinaryIO) -> hints.FileContentLink:
        self.storage[local_file_name] = content
        return hints.FileContentLink(file_path=local_file_name)

    async def put(self, file_meta: hints.UploadedFileMeta, content: BinaryIO) -> hints.FileMeta:
        return hints.FileMeta(
            file_content_link=await self.put_content(file_meta.local_file_name, content),
            guid=file_meta.guid,
            original_filename=file_meta.original_filename,
            extension=file_meta.extension,
            tg_link=file_meta.tg_link,
        )

    async def get(self, file_link: hints.FileContentLink) -> BinaryIO:
        return self.storage[file_link.file_path]
