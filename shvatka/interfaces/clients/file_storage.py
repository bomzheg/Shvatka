from typing import Protocol, BinaryIO

from shvatka.models.dto import scn


class FileStorage(Protocol):
    async def put(self, file_meta: scn.UploadedFileMeta, content: BinaryIO) -> scn.FileMeta:
        raise NotImplementedError

    async def get(self, file_link: scn.FileContentLink) -> BinaryIO:
        raise NotImplementedError

    async def put_content(self, local_file_name: str, content: BinaryIO) -> scn.FileContentLink:
        raise NotImplementedError
