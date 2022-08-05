from dataclasses import dataclass

from app.models.dto.scn.level import LeveScenario


@dataclass
class GameScenario:
    name: str
    levels: list[LeveScenario]
