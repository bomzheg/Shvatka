from copy import copy

from aiogram.types import User

from shvatka.models import dto

OLD_HARRY_USERNAME = "tom_riddle_friend"
HARRY_DTO = dto.User(
    tg_id=666,
    first_name="Harry",
    last_name="Potter",
    username="voldemort_killer",
    is_bot=False,
)

HERMIONE_DTO = dto.User(
    tg_id=13,
    first_name="Hermione",
    last_name="Granger",
    username="smart_girl",
    is_bot=False,
)

RON_DTO = dto.User(
    tg_id=777,
    first_name="Ron",
    last_name="Weasley",
    username="red_hair",
    is_bot=False,
)

ROWLING_DTO = dto.User(
    tg_id=1,
    first_name="Joanne",
    last_name="Rowling",
    is_bot=False,
)


def create_tg_user(
    id_: int = HARRY_DTO.tg_id, username: str = HARRY_DTO.username,
    first_name: str = HARRY_DTO.first_name, last_name: str = HARRY_DTO.last_name,
) -> User:
    return User(
        id=id_,
        username=username,
        first_name=first_name,
        last_name=last_name,
        is_bot=False,
    )


def create_dto_harry() -> dto.User:
    return copy(HARRY_DTO)


def create_dto_hermione() -> dto.User:
    return copy(HERMIONE_DTO)


def create_tg_from_dto(user: dto.User) -> User:
    return User(
        id=user.tg_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_bot=user.is_bot,
    )


def create_dto_ron() -> dto.User:
    return copy(RON_DTO)


def create_dto_rowling() -> dto.User:
    return copy(ROWLING_DTO)
