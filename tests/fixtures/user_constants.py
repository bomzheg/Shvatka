from aiogram.types import User

from app.models import dto, db

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
    return HARRY_DTO


def create_dto_hermione() -> dto.User:
    return HERMIONE_DTO


def create_dto_ron() -> dto.User:
    return RON_DTO


def create_db_user() -> db.User:
    return db.User(
        tg_id=HARRY_DTO.tg_id,
        first_name=HARRY_DTO.first_name,
        last_name=HARRY_DTO.last_name,
        username=HARRY_DTO.last_name,
        is_bot=False,
    )
