from typing import BinaryIO

from shvatka.clients.file_storage import FileStorage
from shvatka.models.dto.scn import FileContentLink


class MemoryFileStorage(FileStorage):
    def __init__(self):
        self.storage = {}

    async def put(self, local_file_name: str, content: BinaryIO) -> FileContentLink:
        self.storage[local_file_name] = content
        return FileContentLink(file_path=local_file_name)

    async def get(self, file_link: FileContentLink) -> BinaryIO:
        return self.storage[file_link.file_path]
