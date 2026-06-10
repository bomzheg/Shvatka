from typing import Protocol

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.models import dto
from shvatka.core.models.dto import hints


class FileInfoMerger(Protocol):
    async def replace_file_info(self, primary: dto.Player, secondary: dto.Player) -> None:
        raise NotImplementedError


class FileInfoGetter(Protocol):
    async def get_by_guid(self, guid: str) -> hints.VerifiableFileMeta:
        raise NotImplementedError


class FileUpserter(Committer, Protocol):
    async def upsert(self, file: hints.FileMeta, author: dto.Player) -> hints.SavedFileMeta:
        raise NotImplementedError

    async def check_author_can_own_guid(self, author: dto.Player, guid: str) -> None:
        raise NotImplementedError
