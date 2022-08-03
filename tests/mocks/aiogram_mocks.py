import typing
from typing import Union

from aiogram import Bot
from aiogram.methods import SendMessage
from aiogram.types import ChatMemberOwner, ChatMemberAdministrator, ChatMemberMember, ChatMemberRestricted, \
    ChatMemberLeft, ChatMemberBanned, Chat, User
from mockito import when

administrators: typing.TypeAlias = list[
    Union[
        ChatMemberOwner,
        ChatMemberAdministrator,
        ChatMemberMember,
        ChatMemberRestricted,
        ChatMemberLeft,
        ChatMemberBanned,
    ]
]

T = typing.TypeVar("T")


def mock_chat_owners(dummy: Bot, chat_id: int, *users: User):
    when(dummy).get_chat_administrators(chat_id).thenReturn(
        mock_coro([ChatMemberOwner(user=user, is_anonymous=False) for user in users])
    )


def mock_get_chat(dummy: Bot, chat: Chat):
    when(dummy).get_chat(chat.id).thenReturn(mock_coro(chat))


def mock_reply(dummy: Bot, message: SendMessage):
    when(dummy).__call__(message).thenReturn(mock_coro(...))


async def mock_coro(value: T) -> T:
    return value
