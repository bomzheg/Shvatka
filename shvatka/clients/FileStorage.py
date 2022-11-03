from io import BytesIO
from typing import Protocol

from shvatka.models.dto.scn import FileContent, FileContentLink


class FileStorage(Protocol):
    async def put(self, file_meta: FileContent, content: BytesIO) -> FileContentLink:
        raise NotImplementedError

    async def get(self, file_link: FileContentLink) -> BytesIO:
        raise NotImplementedError
