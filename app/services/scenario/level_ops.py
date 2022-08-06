import dataclass_factory
from dataclass_factory import Factory

from app.models.dto.scn.level import LevelScenario
from app.utils.exceptions import ScenarioNotCorrect


def load_level(dct: dict, dcf: Factory) -> LevelScenario:
    try:
        return dcf.load(dct, LevelScenario)
    except dataclass_factory.PARSER_EXCEPTIONS:
        raise ScenarioNotCorrect(notify_user="невалидный уровень")
