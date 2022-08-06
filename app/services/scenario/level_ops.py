from dataclass_factory import Factory

from app.models.dto.scn.level import LeveScenario


def load_level(dct: dict, dcf: Factory) -> LeveScenario:
    return dcf.load(dct, LeveScenario)
