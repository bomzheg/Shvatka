from zipfile import Path as ZipPath

from shvatka.utils import exceptions
from tgbot.models.parsed_zip import ParsedZip


def unpack_scn(zip_file: ZipPath) -> ParsedZip:
    scn = None
    files = {}
    for file in zip_file.iterdir():
        if file.is_file():
            if is_filename_equals(file.name, ".yaml"):
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


def is_filename_equals(
    filename: str, example_filename: str = None, example_extension: str = ""
) -> bool:
    if example_filename is None:
        return filename.endswith(example_extension)
    return filename == example_filename + example_extension

