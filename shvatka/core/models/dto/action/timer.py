import abc
import logging
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
from .interface import EffectsDecision, NoActionDecision, EffectsCondition

logger = logging.getLogger(__name__)


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
    action_time: timedelta


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
        if state.current_level_time_id != state.started_level_time_id:
            logger.debug(
                "current lt %s is different from started lt %s, so skip",
                state.current_level_time_id,
                state.started_level_time_id,
            )
            return NoActionDecision()
        current_td = action.now - state.started_at
        if not self.should_execute(current_td):
            logger.debug(
                "%r lt correct but time: (now: %s - start_at: %s) = %s > action_time: %s",
                self,
                action.now,
                state.started_at,
                current_td,
                self.get_action_time(),
            )
            return NoActionDecision()
        decision = self.get_decision()
        if decision.type == DecisionType.EFFECTS:
            if isinstance(decision, LevelTimerEffectsDecision):
                if state.contains_effects(decision.effects):
                    logger.debug(
                        "effect %s already in applied %s", decision.effects, state.applied_effects
                    )
                    return NoActionDecision()
            else:
                raise NotImplementedError(
                    f"decision should contains effects "
                    f"but class is unknown here: {type(decision)}"
                )
        return decision


@dataclass(kw_only=True, frozen=True)
class LevelTimerEffectsCondition(LevelTimerCondition, EffectsCondition):
    """
    action_time - minutes
    """

    action_time: int
    effects: Effects
    type: Literal["EFFECTS_TIMER"] = ConditionType.EFFECTS_TIMER.name

    def get_action_time(self) -> timedelta:
        return timedelta(minutes=self.action_time)

    def get_decision(self) -> Decision:
        return LevelTimerEffectsDecision(
            type=DecisionType.EFFECTS,
            effects=self.effects,
            action_time=timedelta(minutes=self.action_time),
        )
