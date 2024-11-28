from dataclasses import dataclass
from typing import Literal, Sequence, overload

from shvatka.core.models.dto.scn.action.interface import DecisionType, Decision


@dataclass
class NotImplementedActionDecision(Decision):
    type: Literal[DecisionType.NOT_IMPLEMENTED] = DecisionType.NOT_IMPLEMENTED


class Decisions(Sequence[Decision]):
    def __init__(self, decisions: list[Decision]):
        self.decisions = decisions

    @overload
    def __getitem__(self, index: int) -> Decision:
        return self.decisions[index]

    @overload
    def __getitem__(self, index: slice) -> Sequence[Decision]:
        return self.decisions[index]

    def __getitem__(self, index):
        return self.decisions[index]

    def __len__(self):
        return len(self.decisions)

    def __iter__(self):
        return iter(self.decisions)

    def get_significant(self) -> "Decisions":
        return self.get_all_except(DecisionType.NOT_IMPLEMENTED, DecisionType.NO_ACTION)

    def get_implemented(self) -> "Decisions":
        return self.get_all_except(DecisionType.NOT_IMPLEMENTED)

    def get_all(self, *type_: type) -> "Decisions":
        return Decisions([d for d in self.decisions if isinstance(d, type_)])

    def get_all_except(self, *type_: DecisionType) -> "Decisions":
        return Decisions([d for d in self.decisions if d.type not in type_])

    def get_all_only(self, *type_: DecisionType) -> "Decisions":
        return Decisions([d for d in self.decisions if d.type in type_])
