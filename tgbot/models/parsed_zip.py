from contextlib import contextmanager
from dataclasses import dataclass
from zipfile import Path

import yaml

from shvatka.models.dto.scn.game import RawGameScenario


@dataclass
class ParsedZip:
    scn: Path
    files: dict[str, Path]

    @contextmanager
    def open(self):
        contents = {}
        try:
            for guid, path in self.files.items():
                contents[guid]: path.open()
            yield RawGameScenario(scn=yaml.safe_load(self.scn), files=contents)
        finally:
            for file in contents.values():
                file.close()
