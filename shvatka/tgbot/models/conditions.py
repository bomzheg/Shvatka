from typing import Sequence

from shvatka.core.models.dto import scn
from shvatka.core.models.dto.action import AnyCondition


class IncompleteConditions(scn.Conditions):
    def __init__(self, conditions: Sequence[AnyCondition]):
        self.conditions: Sequence[AnyCondition] = conditions
