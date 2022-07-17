from app.models import dto, db


def assert_dto_chat(expected: dto.Chat, actual: dto.Chat):
    assert expected.tg_id == actual.tg_id
    assert expected.username == actual.username
    assert expected.title == expected.title
    assert expected.type == expected.type


def assert_db_chat(expected: db.Chat, actual: db.Chat):
    assert expected.tg_id == actual.tg_id
    assert expected.username == actual.username
    assert expected.title == expected.title
    assert expected.type == expected.type
