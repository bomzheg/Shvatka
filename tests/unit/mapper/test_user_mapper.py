from shvatka.core.models import dto
from tests.fixtures.user_constants import create_dto_harry, create_tg_user


def test_from_aiogram_to_dto():
    source = create_tg_user()
    expected = create_dto_harry()
    actual = dto.User.from_aiogram(source)
    assert expected == actual
