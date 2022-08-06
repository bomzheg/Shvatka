from dataclasses import dataclass

from app.models.dto.scn.level import LevelScenario


@dataclass
class GameScenario:
    name: str
    levels: list[LevelScenario]
