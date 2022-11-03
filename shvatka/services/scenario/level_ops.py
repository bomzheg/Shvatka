import dataclass_factory
from dataclass_factory import Factory

from shvatka.models.dto.scn import TimeHint
from shvatka.models.dto.scn.hint_part import FileMixin
from shvatka.models.dto.scn.level import LevelScenario
from shvatka.utils.exceptions import ScenarioNotCorrect, FileNotFound


def load_level(dct: dict, dcf: Factory) -> LevelScenario:
    try:
        return dcf.load(dct, LevelScenario)
    except dataclass_factory.PARSER_EXCEPTIONS:
        raise ScenarioNotCorrect(notify_user="невалидный уровень")


def check_all_files_saved(level: LevelScenario, guids: set[str]):
    for hints in level.time_hints:
        check_all_files_in_time_hint_saved(hints, guids)


def check_all_files_in_time_hint_saved(hints: TimeHint, guids: set[str]):
    for hint in hints.hint:
        if isinstance(hint, FileMixin):
            if hint.file_guid not in guids:
                raise FileNotFound(text=f"not found {hint.file_guid} in files")
