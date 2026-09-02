from typing import BinaryIO, Protocol

from shvatka.core.models import dto
from shvatka.core.models.dto import hints


class FileGateway(Protocol):
    async def put(
        self,
        file_meta: hints.UploadedFileMeta,
        content: BinaryIO,
        author: dto.Player,
        force: bool = False,
    ):
        """Store the file, uploading it to telegram first if it has no ``tg_link`` yet.

        If telegram rejects the upload, ``force=False`` (the default) lets
        ``FileRejectedByTelegram`` propagate and nothing is stored. With
        ``force=True`` the rejection is swallowed and the file is stored anyway,
        without a ``file_id`` — it will be sent by content the first time it is
        shown in a game.
        """
        raise NotImplementedError

    async def get(self, file_link: hints.FileMeta) -> BinaryIO:
        raise NotImplementedError


class FileStorage(Protocol):
    async def put(
        self,
        file_meta: hints.UploadedFileMeta,
        content: BinaryIO,
        options: hints.FileUploadOptions = hints.DEFAULT_UPLOAD_OPTIONS,
    ) -> hints.FileMeta:
        raise NotImplementedError

    async def get(self, file_link: hints.FileContentLink) -> BinaryIO:
        raise NotImplementedError

    async def put_content(self, local_file_name: str, content: BinaryIO) -> hints.FileContentLink:
        raise NotImplementedError

    async def exists(self, file_link: hints.FileContentLink) -> bool:
        raise NotImplementedError

    async def delete(self, file_link: hints.FileContentLink) -> None:
        """Remove the content. Deleting what is already gone is not an error."""
        raise NotImplementedError

    async def list_files(self) -> list[hints.StoredFile]:
        """Every file the storage holds, with the time its content last changed."""
        raise NotImplementedError
