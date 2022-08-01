from app.models import dto
from tests.fixtures.user_constants import create_tg_user, create_dto_harry


def test_from_aiogram_to_dto():
    source = create_tg_user()
    expected = create_dto_harry()
    actual = dto.User.from_aiogram(source)
    assert expected == actual
