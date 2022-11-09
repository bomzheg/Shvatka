from io import BytesIO
from typing import BinaryIO
from zipfile import Path as ZipPath, ZipFile, ZIP_DEFLATED

import yaml

from shvatka.models.dto.scn.game import RawGameScenario
from shvatka.utils import exceptions
from tgbot.models.parsed_zip import ParsedZip


def unpack_scn(zip_file: ZipPath) -> ParsedZip:
    scn = None
    files = {}
    for file in zip_file.iterdir():
        if file.is_file():
            if str(file.name).endswith(".yaml"):
                if scn is not None:
                    raise exceptions.ScenarioNotCorrect(
                        text=f"Zip contains more that one file "
                             f"with name endswith .yaml"
                    )
                scn = file
            else:
                files[file.name.split(".")[0]] = file
    if scn is None:
        raise exceptions.ScenarioNotCorrect(
            text=f"zip contains no one .yaml file"
        )
    return ParsedZip(scn=scn, files=files)


def pack_scn(game: RawGameScenario) -> BinaryIO:
    output = BytesIO()
    with ZipFile(output, "a", ZIP_DEFLATED, False) as zipfile:
        zipfile.writestr("scn.yaml", yaml.dump(game.scn, allow_unicode=True).encode("utf8"))
        for guid, content in game.files.items():
            zipfile.writestr(guid, content.read())
    output.seek(0)
    return output
