from typing import Protocol, BinaryIO

from shvatka.core.models import dto
from shvatka.core.models.dto import hints


class FileGateway(Protocol):
    async def put(self, file_meta: hints.UploadedFileMeta, content: BinaryIO, author: dto.Player):
        raise NotImplementedError

    async def get(self, file_link: hints.FileMeta) -> BinaryIO:
        raise NotImplementedError


class FileStorage(Protocol):
    async def put(self, file_meta: hints.UploadedFileMeta, content: BinaryIO) -> hints.FileMeta:
        raise NotImplementedError

    async def get(self, file_link: hints.FileContentLink) -> BinaryIO:
        raise NotImplementedError

    async def put_content(self, local_file_name: str, content: BinaryIO) -> hints.FileContentLink:
        raise NotImplementedError
