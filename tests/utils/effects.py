from shvatka.core.models.dto import action


def assert_effects_equal(actual: action.Effects, expected: action.Effects) -> None:
    assert actual.level_up == expected.level_up
    assert actual.next_level == expected.next_level
    assert actual.bonus_minutes == expected.bonus_minutes
    assert actual.hints_ == expected.hints_

    assert actual.id
    assert expected.id
