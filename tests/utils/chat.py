from db import models
from shvatka.models import dto


def assert_dto_chat(expected: dto.Chat, actual: dto.Chat):
    assert expected.tg_id == actual.tg_id
    assert expected.username == actual.username
    assert expected.title == expected.title
    assert expected.type == expected.type


def assert_db_chat(expected: models.Chat, actual: models.Chat):
    assert expected.tg_id == actual.tg_id
    assert expected.username == actual.username
    assert expected.title == expected.title
    assert expected.type == expected.type
