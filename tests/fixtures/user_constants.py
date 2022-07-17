from aiogram.types import User

from app.models import dto, db

ID = 666
FIRST_NAME = "Harry"
LAST_NAME = "Potter"
USERNAME = "voldemort_killer"


def create_tg_user() -> User:
    return User(
        id=ID,
        username=USERNAME,
        first_name=FIRST_NAME,
        last_name=LAST_NAME,
        is_bot=False,
    )


def create_dto_user() -> dto.User:
    return dto.User(
        tg_id=ID,
        first_name=FIRST_NAME,
        last_name=LAST_NAME,
        username=USERNAME,
        is_bot=False,
    )


def create_db_user() -> db.User:
    return db.User(
        tg_id=ID,
        first_name=FIRST_NAME,
        last_name=LAST_NAME,
        username=USERNAME,
        is_bot=False,
    )
