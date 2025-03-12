from shvatka.core.models.dto import scn, action, hints


def render_bonus_hints(level: scn.LevelScenario) -> dict[tuple[str, ...], list[hints.AnyHint]]:
    result: dict[tuple[str, ...], list[hints.AnyHint]] = {}
    for cond in level.conditions:
        if not isinstance(cond, action.KeyBonusHintCondition):
            continue
        result[tuple(cond.keys)] = cond.bonus_hint
    return result
