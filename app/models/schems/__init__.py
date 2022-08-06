from dataclass_factory import NameStyle

from app.models.dto.scn.level import LevelScenario
from .level import LevelSchema

__all__ = ["LevelSchema"]
schemas = {LevelScenario: LevelSchema(name_style=NameStyle.kebab)}