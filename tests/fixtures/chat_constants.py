from copy import copy

from aiogram import types as tg

from shvatka.core.models import dto
from shvatka.core.models.enums.chat_type import ChatType
from shvatka.infrastructure.db import models

GRYFFINDOR_USERNAME = "gryffindor_rules"

GRYFFINDOR_TITLE = "Gryffindor living room"

NEW_CHAT_ID = -10048
GRYFFINDOR_CHAT_DTO = dto.Chat(
    tg_id=42,
    type=ChatType.group,
    username=GRYFFINDOR_USERNAME,
    title=GRYFFINDOR_TITLE,
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
    title: str = GRYFFINDOR_TITLE,
    type_: ChatType = GRYFFINDOR_CHAT_DTO.type,
    username: str = GRYFFINDOR_USERNAME,
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


def chat_to_full_chat(chat: tg.Chat) -> tg.ChatFullInfo:
    return tg.ChatFullInfo(
        id=chat.id,
        title=chat.title,
        type=chat.type,
        username=chat.username,
        first_name=chat.first_name,
        last_name=chat.last_name,
        accent_color_id=0,
        max_reaction_count=3,
        accepted_gift_types=tg.AcceptedGiftTypes(
            unlimited_gifts=True,
            limited_gifts=True,
            unique_gifts=True,
            premium_subscription=False,
        ),
    )


def create_db_chat():
    return models.Chat(
        tg_id=GRYFFINDOR_CHAT_DTO.tg_id,
        type=GRYFFINDOR_CHAT_DTO.type,
        username=GRYFFINDOR_CHAT_DTO.username,
        title=GRYFFINDOR_CHAT_DTO.title,
    )
