import typing
from contextlib import contextmanager
from dataclasses import dataclass
from typing import ContextManager, BinaryIO, TextIO
from zipfile import Path

import yaml

from .game import RawGameScenario


@dataclass
class ParsedZip:
    scn: Path
    files: dict[str, Path]
    results: Path | None = None

    @contextmanager  # type: ignore[arg-type]
    def open(self) -> ContextManager[RawGameScenario]:  # type: ignore[misc]
        contents: dict[str, BinaryIO] = {}
        results = None
        try:
            for guid, path in self.files.items():
                contents[guid] = typing.cast(BinaryIO, path.open("rb"))
            results = self.open_results_if_present()
            with self.scn.open("r", encoding="utf8") as scn_f:
                yield RawGameScenario(
                    scn=yaml.safe_load(scn_f),
                    files=contents,
                    stat=yaml.safe_load(results) if results else None,
                )
        finally:
            for file in contents.values():
                file.close()
            if results:
                results.close()

    def open_results_if_present(self) -> TextIO | None:
        if self.results:
            return typing.cast(TextIO, self.results.open("r", encoding="uft8"))
        else:
            return None
