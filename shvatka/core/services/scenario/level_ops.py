from adaptix import Retort
from adaptix.load_error import LoadError

from shvatka.core.models.dto import scn
from shvatka.core.utils import exceptions


def load_level(dct: dict, retort: Retort) -> scn.LevelScenario:
    try:
        return retort.load(dct, scn.LevelScenario)
    except LoadError as e:
        raise exceptions.ScenarioNotCorrect(notify_user="невалидный уровень") from e
