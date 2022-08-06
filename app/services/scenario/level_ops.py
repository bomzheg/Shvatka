from dataclass_factory import Factory

from app.models.dto.scn.level import LevelScenario


def load_level(dct: dict, dcf: Factory) -> LevelScenario:
    return dcf.load(dct, LevelScenario)
