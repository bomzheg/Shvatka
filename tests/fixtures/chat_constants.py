from copy import copy

from aiogram import types as tg

from src.core.models import dto
from src.core.models.enums.chat_type import ChatType
from src.infrastructure.db import models

NEW_CHAT_ID = -10048
GRYFFINDOR_CHAT_DTO = dto.Chat(
    tg_id=42,
    type=ChatType.group,
    username="gryffindor_rules",
    title="Gryffindor living room",
)
SLYTHERIN_CHAT_DTO = dto.Chat(
    tg_id=9,
    type=ChatType.supergroup,
    username="slytherin_cool",
    title="Slytherin underground",
)


def create_gryffindor_dto_chat():
    return copy(GRYFFINDOR_CHAT_DTO)


def create_slytherin_dto_chat():
    return copy(SLYTHERIN_CHAT_DTO)


def create_tg_chat(
    id_: int = GRYFFINDOR_CHAT_DTO.tg_id,
    title: str = GRYFFINDOR_CHAT_DTO.title,
    type_: ChatType = GRYFFINDOR_CHAT_DTO.type,
    username: str = GRYFFINDOR_CHAT_DTO.username,
    first_name: str | None = None,
    last_name: str | None = None,
):
    return tg.Chat(
        id=id_,
        title=title,
        type=type_.name,
        username=username,
        first_name=first_name,
        last_name=last_name,
    )


def create_db_chat():
    return models.Chat(
        tg_id=GRYFFINDOR_CHAT_DTO.tg_id,
        type=GRYFFINDOR_CHAT_DTO.type,
        username=GRYFFINDOR_CHAT_DTO.username,
        title=GRYFFINDOR_CHAT_DTO.title,
    )
