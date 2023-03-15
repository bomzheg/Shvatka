import typing
from contextlib import contextmanager
from dataclasses import dataclass
from typing import ContextManager, BinaryIO
from zipfile import Path

import yaml

from .game import RawGameScenario


@dataclass
class ParsedZip:
    scn: Path
    files: dict[str, Path]

    @contextmanager  # type: ignore[arg-type]
    def open(self) -> ContextManager[RawGameScenario]:  # type: ignore[misc]
        contents: dict[str, BinaryIO] = {}
        try:
            for guid, path in self.files.items():
                contents[guid] = typing.cast(BinaryIO, path.open("rb"))
            with self.scn.open("r", encoding="utf8") as f:
                yield RawGameScenario(scn=yaml.safe_load(f), files=contents)
        finally:
            for file in contents.values():
                file.close()
