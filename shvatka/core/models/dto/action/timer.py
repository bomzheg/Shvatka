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


@dataclass
class LevelTimerAction(Action):
    now: datetime


@dataclass
class LevelTimerState(State):
    started_level_time_id: int
    current_level_time_id: int
    applied_effects: list[Effects]
    started_at: datetime


@dataclass(kw_only=True, frozen=True)
class LevelTimerDecision(Decision):
    type: DecisionType


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
            return self.get_decision()
        else:
            return LevelTimerDecision(type=DecisionType.NO_ACTION)


@dataclass
class LevelTimerWinCondition(LevelTimerCondition):
    action_time: timedelta
    type: Literal["WIN_TIMER"] = ConditionType.WIN_TIMER.name

    def get_action_time(self) -> timedelta:
        return self.action_time

    def get_decision(self) -> Decision:
        return LevelTimerDecision(type=DecisionType.LEVEL_UP)
