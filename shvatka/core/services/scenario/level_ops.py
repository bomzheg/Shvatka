from adaptix import Retort
from adaptix.load_error import LoadError

from shvatka.core.models.dto import scn, action, hints
from shvatka.core.utils import exceptions


def load_level(dct: dict, retort: Retort) -> scn.LevelScenario:
    try:
        return retort.load(dct, scn.LevelScenario)
    except LoadError as e:
        raise exceptions.ScenarioNotCorrect(notify_user="невалидный уровень") from e


def check_all_files_saved(level: scn.LevelScenario, guids: set[str]):
    for hints_ in level.time_hints:
        check_all_files_in_hints_saved(hints_.hint, guids)
    for condition in level.conditions:
        if isinstance(condition, action.KeyBonusHintCondition):
            check_all_files_in_hints_saved(condition.bonus_hint, guids)


def check_all_files_in_hints_saved(hints_: list[hints.AnyHint], guids: set[str]):
    for hint in hints_:
        if isinstance(hint, hints.FileMixin) and hint.file_guid not in guids:
            raise exceptions.FileNotFound(text=f"not found {hint.file_guid} in files")
