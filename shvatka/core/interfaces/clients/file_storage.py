from typing import BinaryIO, Protocol

from shvatka.core.models import dto
from shvatka.core.models.dto import hints


class FileGateway(Protocol):
    async def put(self, file_meta: hints.UploadedFileMeta, content: BinaryIO, author: dto.Player):
        """Store the file, uploading it to telegram first if it has no ``tg_link`` yet.

        Raises ``FileRejectedByTelegram`` when telegram refuses the upload, and
        stores nothing: a file the game can't deliver is not a file worth
        keeping. A caller that wants it anyway catches that and stores it
        itself (see ``UploadGameFileInteractor``).
        """
        raise NotImplementedError

    async def get(self, file_link: hints.FileMeta) -> BinaryIO:
        raise NotImplementedError

    async def renew_file_id(self, author: dto.Player, file_meta: hints.SavedFileMeta) -> None:
        """Send a stored file to telegram again and remember the fresh file_id.

        Raises ``FileRejectedByTelegram`` when telegram refuses it.
        """
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
