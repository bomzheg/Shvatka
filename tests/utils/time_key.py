from shvatka.core.models import dto


def assert_time_key(expected: dto.KeyTime, actual: dto.KeyTime):
    assert expected.text == actual.text
    assert expected.player == actual.player
    assert expected.team == actual.team
    assert expected.level_number == actual.level_number
    assert expected.type_ == actual.type_
    assert expected.is_duplicate == actual.is_duplicate
