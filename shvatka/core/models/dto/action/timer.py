import abc
from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import Literal

from shvatka.core.models.dto.action import (
    Condition,
    Action,
    State,
    StateHolder,
    Decision,
    NotImplementedActionDecision,
    DecisionType,
    ConditionType,
)
from .effects import Effects
from .interface import EffectsDecision, NoActionDecision


@dataclass
class LevelTimerAction(Action):
    now: datetime


@dataclass
class LevelTimerState(State):
    started_level_time_id: int
    current_level_time_id: int
    applied_effects: list[Effects]
    started_at: datetime

    def contains_effects(self, effects: Effects) -> bool:
        return any(map(lambda e: e.id == effects.id, self.applied_effects))


@dataclass(kw_only=True, frozen=True)
class LevelTimerDecision(Decision):
    type: DecisionType


@dataclass(kw_only=True, frozen=True)
class LevelTimerEffectsDecision(LevelTimerDecision, EffectsDecision):
    pass


class LevelTimerCondition(Condition, metaclass=abc.ABCMeta):
    def get_action_time(self) -> timedelta:
        raise NotImplementedError

    def should_execute(self, from_start: timedelta) -> bool:
        return self.get_action_time() <= from_start

    def get_decision(self) -> Decision:
        raise NotImplementedError

    def check(self, action: Action, state_holder: StateHolder) -> Decision:
        if not isinstance(action, LevelTimerAction):
            return NotImplementedActionDecision()
        state = state_holder.get(LevelTimerState)
        if (
            self.should_execute(action.now - state.started_at)
            and state.current_level_time_id == state.started_level_time_id
        ):
            decision = self.get_decision()
            if decision.type == DecisionType.EFFECTS:
                if isinstance(decision, LevelTimerEffectsDecision):
                    if state.contains_effects(decision.effects):
                        return NoActionDecision()
                else:
                    raise NotImplementedError(
                        f"decision should contains effects "
                        f"but class is unknown here: {type(decision)}"
                    )
            return decision
        else:
            return NoActionDecision()


@dataclass
class LevelTimerEffectsCondition(LevelTimerCondition):
    action_time: timedelta
    effects: Effects
    type: Literal["EFFECTS"] = ConditionType.EFFECTS.name

    def get_action_time(self) -> timedelta:
        return self.action_time

    def get_decision(self) -> Decision:
        return LevelTimerEffectsDecision(type=DecisionType.EFFECTS, effects=self.effects)
