from typing import Sequence

from shvatka.core.models.dto import scn, action
from shvatka.core.models.dto.action import AnyCondition


class IncompleteConditions(scn.Conditions):
    def __init__(self, conditions: Sequence[AnyCondition]):
        self.conditions: Sequence[AnyCondition] = conditions

    def replace_default_keys(self, keys: set[action.SHKey]) -> "IncompleteConditions":
        other_conditions = [
            c
            for c in self.conditions
            if not isinstance(c, action.KeyWinCondition) or c.next_level is not None
        ]
        return IncompleteConditions([*other_conditions, action.KeyWinCondition(keys)])

    def replace_bonus_hint_conditions(
        self, conditions: list[action.KeyBonusHintCondition]
    ) -> "IncompleteConditions":
        other_conditions = [
            c for c in self.conditions if not isinstance(c, action.KeyBonusHintCondition)
        ]
        return IncompleteConditions([*other_conditions, *conditions])

    def replace_routed_conditions(
        self, conditions: list[action.KeyWinCondition]
    ) -> "IncompleteConditions":
        other_conditions = [
            c
            for c in self.conditions
            if not isinstance(c, action.KeyWinCondition) or c.next_level is None
        ]
        return IncompleteConditions([*other_conditions, *conditions])

    def replace_effects_conditions(
        self, conditions: list[action.KeyEffectsCondition]
    ) -> "IncompleteConditions":
        other_conditions = [
            c for c in self.conditions if not isinstance(c, action.KeyEffectsCondition)
        ]
        return IncompleteConditions([*other_conditions, *conditions])
