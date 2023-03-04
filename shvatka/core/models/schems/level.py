from dataclass_factory import Schema, validate

from shvatka.core.models.dto import scn
from shvatka.core.models.dto.scn.level import SHKey
from shvatka.core.utils.exceptions import ScenarioNotCorrect
from shvatka.core.utils.input_validation import is_level_id_correct, is_multiple_keys_normal
from shvatka.core.views.texts import INVALID_KEY_ERROR


class LevelSchema(Schema[scn.LevelScenario]):
    @validate("id")
    def validate_id(self, data: str) -> str:
        if not is_level_id_correct(data):
            raise ScenarioNotCorrect(name_id=data, text=f"name_id ({data}) not correct")
        return data

    @validate("keys")
    def validate_keys(self, data: set[SHKey]):
        if not is_multiple_keys_normal(data):
            raise ScenarioNotCorrect(notify_user=INVALID_KEY_ERROR, text="invalid keys")
        return data
