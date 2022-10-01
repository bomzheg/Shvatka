from copy import copy

from aiogram import types as tg

from db import models
from shvatka.models import dto
from shvatka.models.enums.chat_type import ChatType

NEW_CHAT_ID = -10048
AWESOME_CHAT_DTO = dto.Chat(
    tg_id=42,
    type=ChatType.group,
    username="ultra_chat",
    title="My awesome chat",
)
NOT_SO_GOOD_CHAT_DTO = dto.Chat(
    tg_id=9,
    type=ChatType.supergroup,
    username="dummy_group",
    title="boring chat",
)


def create_dto_chat():
    return copy(AWESOME_CHAT_DTO)


def create_another_chat():
    return copy(NOT_SO_GOOD_CHAT_DTO)


def create_tg_chat(
    id_: int = AWESOME_CHAT_DTO.tg_id, title: str = AWESOME_CHAT_DTO.title,
    type_: ChatType = AWESOME_CHAT_DTO.type, username: str = AWESOME_CHAT_DTO.username,
):
    return tg.Chat(
        id=id_,
        title=title,
        type=type_.name,
        username=username,
    )


def create_db_chat():
    return models.Chat(
        tg_id=AWESOME_CHAT_DTO.tg_id,
        type=AWESOME_CHAT_DTO.type,
        username=AWESOME_CHAT_DTO.username,
        title=AWESOME_CHAT_DTO.title,
    )
