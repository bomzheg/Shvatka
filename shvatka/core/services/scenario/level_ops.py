from adaptix import Retort
from adaptix.load_error import LoadError

from shvatka.core.models.dto import scn
from shvatka.core.models.dto import hints
from shvatka.core.utils import exceptions


def load_level(dct: dict, retort: Retort) -> scn.LevelScenario:
    try:
        return retort.load(dct, scn.LevelScenario)
    except LoadError as e:
        raise exceptions.ScenarioNotCorrect(notify_user="невалидный уровень") from e


def check_all_files_saved(level: scn.LevelScenario, guids: set[str]):
    for hints_ in level.time_hints:
        check_all_files_in_time_hint_saved(hints_, guids)


def check_all_files_in_time_hint_saved(hints_: hints.TimeHint, guids: set[str]):
    for hint in hints_.hint:
        if isinstance(hint, hints.FileMixin) and hint.file_guid not in guids:
            raise exceptions.FileNotFound(text=f"not found {hint.file_guid} in files")
