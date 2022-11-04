from dataclass_factory import NameStyle, Schema

from shvatka.models.dto.scn.level import LevelScenario
from .level import LevelSchema

__all__ = ["LevelSchema", "schemas"]

from ..dto.scn import PhotoHint, FileContent, TgLink, FileContentLink

schemas = {
    LevelScenario: LevelSchema(name_style=NameStyle.kebab),
    PhotoHint: Schema(name_style=NameStyle.kebab),
    FileContent: Schema(name_style=NameStyle.kebab),
    TgLink: Schema(name_style=NameStyle.kebab),
    FileContentLink: Schema(name_style=NameStyle.kebab),
}
