from typing import Protocol, BinaryIO

from shvatka.models.dto.scn import FileContent, FileContentLink


class FileStorage(Protocol):
    async def put(self, file_meta: FileContent, content: BinaryIO) -> FileContentLink:
        raise NotImplementedError

    async def get(self, file_link: FileContentLink) -> BinaryIO:
        raise NotImplementedError
