from app.models import dto


def assert_user(expected: dto.User, actual: dto.User):
    assert expected.tg_id == actual.tg_id
    assert expected.username == actual.username
    assert expected.first_name == actual.first_name
    assert expected.last_name == actual.last_name
    assert expected.is_bot == actual.is_bot
