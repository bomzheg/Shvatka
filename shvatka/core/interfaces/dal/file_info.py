from typing import Protocol

from shvatka.core.models import dto


class FileInfoMerger(Protocol):
    async def replace_file_info(self, primary: dto.Player, secondary: dto.Player) -> None:
        raise NotImplementedError
