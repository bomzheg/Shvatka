from typing import Sequence

from shvatka.core.models.dto import scn, action
from shvatka.core.models.dto.action import AnyCondition


class IncompleteConditions(scn.Conditions):
    def __init__(self, conditions: Sequence[AnyCondition]):
        scn.Conditions.validate_keys_unique(conditions)
        scn.Conditions.validate_unique_effects(conditions)
        force_level_up_time = scn.Conditions.get_force_level_up(conditions)
        timers = scn.Conditions.get_conditions_type(conditions, action.LevelTimerEffectsCondition)
        scn.Conditions.validate_timers_times_is_unique(timers)
        scn.Conditions.validate_all_timers_le_force(timers, force_level_up_time)
        self.conditions: Sequence[AnyCondition] = conditions

    def replace_default_keys(self, keys: set[action.SHKey]) -> "IncompleteConditions":
        other_conditions = [
            c for c in self.conditions if not isinstance(c, action.KeyWinCondition)
        ]
        return IncompleteConditions([*other_conditions, action.KeyWinCondition(keys)])

    def replace_effects_conditions(
        self, conditions: list[action.KeyEffectsCondition]
    ) -> "IncompleteConditions":
        other_conditions = [
            c for c in self.conditions if not isinstance(c, action.KeyEffectsCondition)
        ]
        return IncompleteConditions([*other_conditions, *conditions])
