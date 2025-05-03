from io import BytesIO
from typing import Protocol

from shvatka.core.scenario import dto


class TransitionsPrinter(Protocol):
    def print(self, transitions: dto.Transitions) -> BytesIO:
        raise NotImplementedError
