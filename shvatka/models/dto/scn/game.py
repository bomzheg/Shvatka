from dataclasses import dataclass

from shvatka.models.dto.scn.level import LevelScenario


@dataclass
class GameScenario:
    name: str
    levels: list[LevelScenario]
