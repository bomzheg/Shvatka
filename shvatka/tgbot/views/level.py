from typing import Sequence


from shvatka.core.models.dto import scn, action, hints
from shvatka.tgbot.views.keys import render_keys


def render_bonus_hints(level: scn.LevelScenario) -> dict[tuple[str, ...], Sequence[hints.AnyHint]]:
    result: dict[tuple[str, ...], Sequence[hints.AnyHint]] = {}
    for cond in level.conditions:
        if isinstance(cond, action.KeyEffectsCondition) and cond.effects.hints_:
            result[tuple(cond.keys)] = cond.effects.hints_
    return result


def render_effects_key_caption(
    effect_key: action.KeyEffectsCondition,
) -> tuple[str, Sequence[hints.AnyHint]]:
    text = f"Ключ:\n{render_keys(effect_key.keys)}\n"
    effect_caption, hints_ = render_effects_caption(effect_key.effects)
    return text + effect_caption, hints_


def render_effects_timer_caption(
    effect_timer: action.LevelTimerEffectsCondition,
) -> tuple[str, Sequence[hints.AnyHint]]:
    text = f"Таймер срабатывает в {effect_timer.action_time} мин.\n"
    effect_caption, hints_ = render_effects_caption(effect_timer.effects)
    return text + effect_caption, hints_


def render_effects_caption(effects: action.Effects) -> tuple[str, Sequence[hints.AnyHint]]:
    text = ""
    if effects.is_no_effects():
        return "Не имеет эффектов", []
    if effects.is_routed_level_up():
        text += f"переход на уровень {effects.next_level}\n"
    elif effects.level_up:
        text += "переход на следующий уровень\n"
    if bonus := effects.bonus_minutes:
        if bonus > 0:
            text += f"Приносит бонус {bonus} мин.\n"
        else:
            text += f"Накладывает штраф {abs(bonus)} мин.\n"
    if effects.hints_:
        text += "Даёт бонусные подсказки:"
    return text, effects.hints_
