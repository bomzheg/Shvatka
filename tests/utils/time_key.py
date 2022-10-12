from shvatka.models import dto


def assert_time_key(expected: dto.KeyTime, actual: dto.KeyTime):
    assert expected.text == actual.text
    assert expected.player == actual.player
    assert expected.is_correct == actual.is_correct
    assert expected.is_duplicate == actual.is_duplicate
