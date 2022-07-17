from aiogram import types as tg

from app.enums.chat_type import ChatType
from app.models import dto, db

CHAT_ID = 42
NEW_CHAT_ID = -10048
TITLE = "My awesome chat"
TYPE = ChatType.group
USERNAME = "ultra_chat"


def create_dto_chat():
    expected = dto.Chat(
        tg_id=CHAT_ID,
        type=TYPE,
        username=USERNAME,
        title=TITLE,
    )
    return expected


def create_tg_chat():
    source = tg.Chat(
        id=CHAT_ID,
        title=TITLE,
        type=TYPE.name,
        username=USERNAME,
    )
    return source


def create_db_chat():
    return db.Chat(
        tg_id=CHAT_ID,
        type=TYPE,
        username=USERNAME,
        title=TITLE,
    )
