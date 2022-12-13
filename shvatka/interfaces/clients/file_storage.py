from typing import Protocol, BinaryIO

from shvatka.models.dto.scn import FileContentLink


class FileStorage(Protocol):
    async def put(self, local_file_name: str, content: BinaryIO) -> FileContentLink:
        raise NotImplementedError

    async def get(self, file_link: FileContentLink) -> BinaryIO:
        raise NotImplementedError
