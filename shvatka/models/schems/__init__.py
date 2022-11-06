from dataclass_factory import NameStyle

from shvatka.models.dto.scn.level import LevelScenario
from .level import LevelSchema

__all__ = ["LevelSchema", "schemas"]


schemas = {
    LevelScenario: LevelSchema(name_style=NameStyle.kebab),
}
