from datetime import datetime
from typing import BinaryIO

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.models.dto import hints
from shvatka.core.utils.datetime_utils import tz_utc


class MemoryFileStorage(FileStorage):
    def __init__(self) -> None:
        self.storage: dict[str, BinaryIO] = {}
        self.modified_at: dict[str, datetime] = {}

    async def put_content(self, local_file_name: str, content: BinaryIO) -> hints.FileContentLink:
        self.storage[local_file_name] = content
        self.modified_at[local_file_name] = datetime.now(tz=tz_utc)
        return hints.FileContentLink(file_path=local_file_name)

    async def put(
        self,
        file_meta: hints.UploadedFileMeta,
        content: BinaryIO,
        options: hints.FileUploadOptions = hints.DEFAULT_UPLOAD_OPTIONS,
    ) -> hints.FileMeta:
        return hints.FileMeta(
            file_content_link=await self.put_content(file_meta.local_file_name, content),
            guid=file_meta.guid,
            original_filename=file_meta.original_filename,
            extension=file_meta.extension,
            file_id=file_meta.file_id,
            content_type=file_meta.content_type,
        )

    async def get(self, file_link: hints.FileContentLink) -> BinaryIO:
        return self.storage[file_link.file_path]

    async def exists(self, file_link: hints.FileContentLink) -> bool:
        return file_link.file_path in self.storage

    async def delete(self, file_link: hints.FileContentLink) -> None:
        self.storage.pop(file_link.file_path, None)
        self.modified_at.pop(file_link.file_path, None)

    async def list_files(self) -> list[hints.StoredFile]:
        return [
            hints.StoredFile(
                link=hints.FileContentLink(file_path=path),
                modified_at=self.modified_at[path],
            )
            for path in self.storage
        ]
