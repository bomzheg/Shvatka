from dataclass_factory import Schema, validate

from app.models.dto.scn.level import SHKey
from app.utils.exceptions import ScenarioNotCorrect
from app.utils.input_validation import is_level_id_correct, is_multiple_keys_normal
from app.views.texts import INVALID_KEY_ERROR


class LevelSchema(Schema):

    @validate("id")
    def validate_id(self, data: str) -> str:
        if not is_level_id_correct(data):
            raise ScenarioNotCorrect(
                name_id=data,
                text=f"name_id ({data}) not correct"
            )
        return data

    @validate("keys")
    def validate_keys(self, data: set[SHKey]):
        if not is_multiple_keys_normal(data):
            raise ScenarioNotCorrect(
                notify_text=INVALID_KEY_ERROR,
                text="invalid keys"
            )
        return data
