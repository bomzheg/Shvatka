from shvatka.core.models import dto
from tests.fixtures.chat_constants import create_gryffindor_dto_chat, create_tg_chat


def test_mapper_from_aiogram_to_dto():
    source = create_tg_chat()
    expected = create_gryffindor_dto_chat()
    actual = dto.Chat.from_aiogram(source)
    assert expected == actual
