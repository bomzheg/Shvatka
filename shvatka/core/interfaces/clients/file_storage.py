from typing import Protocol, BinaryIO

from shvatka.core.models import dto
from shvatka.core.models.dto import scn


class FileGateway(Protocol):
    async def put(self, file_meta: scn.UploadedFileMeta, content: BinaryIO, author: dto.Player):
        raise NotImplementedError

    async def get(self, file_link: scn.FileMeta) -> BinaryIO:
        raise NotImplementedError


class FileStorage(Protocol):
    async def put(self, file_meta: scn.UploadedFileMeta, content: BinaryIO) -> scn.FileMeta:
        raise NotImplementedError

    async def get(self, file_link: scn.FileContentLink) -> BinaryIO:
        raise NotImplementedError

    async def put_content(self, local_file_name: str, content: BinaryIO) -> scn.FileContentLink:
        raise NotImplementedError
