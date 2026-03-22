from typing import Sequence

from shvatka.core.models.dto import scn, action, hints


def render_bonus_hints(level: scn.LevelScenario) -> dict[tuple[str, ...], Sequence[hints.AnyHint]]:
    result: dict[tuple[str, ...], Sequence[hints.AnyHint]] = {}
    for cond in level.conditions:
        if isinstance(cond, action.KeyEffectsCondition) and cond.effects.hints_:
            result[tuple(cond.keys)] = cond.effects.hints_
    return result
