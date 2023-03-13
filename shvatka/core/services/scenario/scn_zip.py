from io import BytesIO
from typing import BinaryIO
from zipfile import Path as ZipPath, ZipFile, ZIP_DEFLATED

import yaml

from shvatka.core.models.dto import scn
from shvatka.core.utils import exceptions


def unpack_scn(zip_file: ZipPath) -> scn.ParsedZip:
    scenario = None
    files = {}
    for file in zip_file.iterdir():
        if file.is_file():
            if str(file.name).endswith(".yaml"):
                if scenario is not None:
                    raise exceptions.ScenarioNotCorrect(
                        text="Zip contains more that one file with name endswith .yaml"
                    )
                scenario = file
            else:
                files[file.name.split(".")[0]] = file
    if scenario is None:
        raise exceptions.ScenarioNotCorrect(text="zip contains no one .yaml file")
    return scn.ParsedZip(scn=scenario, files=files)


def pack_scn(game: scn.RawGameScenario) -> BinaryIO:
    output = BytesIO()
    with ZipFile(output, "a", ZIP_DEFLATED, False) as zipfile:
        zipfile.writestr(
            "scn.yaml",
            yaml.dump(game.scn, allow_unicode=True, sort_keys=False).encode("utf8"),
        )
        for guid, content in game.files.items():
            zipfile.writestr(guid, content.read())
    output.seek(0)
    return output
