import typing
from io import BytesIO
from typing import Protocol

from shvatka.core.scenario import dto


class TransitionsPrinter(Protocol):
    FINISH_NAME: typing.ClassVar[str] = "__finish__"

    def print(self, transitions: dto.Transitions) -> str:
        raise NotImplementedError

    async def render(self, diagram: str) -> BytesIO:
        raise NotImplementedError


class KeysSheetPrinter(Protocol):
    file_extension: typing.ClassVar[str]

    def print_keys_sheet(self, sheet: dto.KeysSheet) -> BytesIO:
        raise NotImplementedError
