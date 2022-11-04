from typing import BinaryIO

from shvatka.clients.file_storage import FileStorage
from shvatka.models.dto.scn import FileContent, FileContentLink


class MemoryFileStorage(FileStorage):
    def __init__(self):
        self.storage = {}

    async def put(self, file_meta: FileContent, content: BinaryIO) -> FileContentLink:
        self.storage[file_meta.guid] = content
        return FileContentLink(file_path=file_meta.guid)

    async def get(self, file_link: FileContentLink) -> BinaryIO:
        return self.storage[file_link.file_path]
