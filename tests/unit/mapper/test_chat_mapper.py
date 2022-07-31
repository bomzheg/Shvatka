from app.models import dto
from tests.fixtures.chat_constants import create_tg_chat, create_dto_chat


def test_mapper_from_aiogram_to_dto():
    source = create_tg_chat()
    expected = create_dto_chat()
    actual = dto.Chat.from_aiogram(source)
    assert expected == actual
