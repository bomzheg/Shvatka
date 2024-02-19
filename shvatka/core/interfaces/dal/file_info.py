from typing import Protocol

from shvatka.core.models import dto
from shvatka.core.models.dto import scn


class FileInfoMerger(Protocol):
    async def replace_file_info(self, primary: dto.Player, secondary: dto.Player) -> None:
        raise NotImplementedError


class FileInfoGetter(Protocol):
    async def get_by_guid(self, guid: str) -> scn.VerifiableFileMeta:
        raise NotImplementedError
