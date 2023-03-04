from dataclass_factory import Schema, validate

from src.shvatka.models.dto import scn
from src.shvatka.models.dto.scn.level import SHKey
from src.shvatka.utils.exceptions import ScenarioNotCorrect
from src.shvatka.utils.input_validation import is_level_id_correct, is_multiple_keys_normal
from src.shvatka.views.texts import INVALID_KEY_ERROR


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
