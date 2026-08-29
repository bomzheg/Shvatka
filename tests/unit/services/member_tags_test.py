from unittest.mock import AsyncMock

import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from shvatka.core.models import dto
from shvatka.tgbot.services.bot_rights import BotRights, ChatRights
from shvatka.tgbot.services.member_tags import MemberTagger, render_tag

PUBLIC_CHAT = -1001
ANOTHER_PUBLIC_CHAT = -1002
CAN_TAG = ChatRights(can_pin_messages=False, can_manage_tags=True)
CANT_TAG = ChatRights(can_pin_messages=True, can_manage_tags=False)


def player(tg_id: int | None = 42) -> dto.Player:
    user = dto.User(tg_id=tg_id, first_name="Harry", is_bot=False) if tg_id is not None else None
    return dto.Player(id=1, can_be_author=False, is_dummy=False, user=user)


def team(name: str = "Gryffindor") -> dto.Team:
    return dto.Team(id=1, name=name, captain=None, is_dummy=False, description=None)


def tagger(*chats: int) -> tuple[MemberTagger, AsyncMock]:
    bot = AsyncMock(Bot)
    config = AsyncMock()
    config.public_chats = list(chats)
    rights = BotRights(bot=AsyncMock(Bot))
    for chat_id in chats:
        rights.save(chat_id, CAN_TAG)
    return MemberTagger(bot=bot, config=config, bot_rights=rights), bot


@pytest.mark.parametrize(
    ("name", "tag"),
    [
        ("Gryffindor", "Gryffindor"),
        ("Орден Феникса", "Орден Феникса"),
        # 16 characters is the limit, the rest is cut off
        ("Отряд Дамблдора", "Отряд Дамблдора"),
        ("Пожиратели смерти", "Пожиратели смерт"),
        # emoji are not allowed in tags
        ("🦁 Gryffindor", "Gryffindor"),
        ("Гриффиндор 🦁🐍", "Гриффиндор"),
        ("👨‍👩‍👧 Семья", "Семья"),
        ("🖐🏻 Пятеро", "Пятеро"),
        # nothing left to show
        ("🦁🐍", None),
        ("", None),
    ],
)
def test_render_tag(name: str, tag: str | None) -> None:
    assert tag == render_tag(name)


@pytest.mark.asyncio
async def test_tag_set_in_every_public_chat() -> None:
    member_tagger, bot = tagger(PUBLIC_CHAT, ANOTHER_PUBLIC_CHAT)

    await member_tagger.sync(player(), team())

    assert [
        {"chat_id": PUBLIC_CHAT, "user_id": 42, "tag": "Gryffindor"},
        {"chat_id": ANOTHER_PUBLIC_CHAT, "user_id": 42, "tag": "Gryffindor"},
    ] == [call.kwargs for call in bot.set_chat_member_tag.await_args_list]


@pytest.mark.asyncio
async def test_tag_cleared_without_team() -> None:
    member_tagger, bot = tagger(PUBLIC_CHAT)

    await member_tagger.sync(player(), None)

    bot.set_chat_member_tag.assert_awaited_once_with(chat_id=PUBLIC_CHAT, user_id=42, tag=None)


@pytest.mark.asyncio
async def test_player_without_telegram_not_tagged() -> None:
    member_tagger, bot = tagger(PUBLIC_CHAT)

    await member_tagger.sync(player(tg_id=None), team())

    assert bot.set_chat_member_tag.await_count == 0


@pytest.mark.asyncio
async def test_chat_without_rights_skipped() -> None:
    member_tagger, bot = tagger(PUBLIC_CHAT, ANOTHER_PUBLIC_CHAT)
    member_tagger.bot_rights.save(PUBLIC_CHAT, CANT_TAG)

    await member_tagger.sync(player(), team())

    bot.set_chat_member_tag.assert_awaited_once_with(
        chat_id=ANOTHER_PUBLIC_CHAT, user_id=42, tag="Gryffindor"
    )


@pytest.mark.asyncio
async def test_telegram_error_not_raised() -> None:
    # the player may be not a member of the public chat at all
    member_tagger, bot = tagger(PUBLIC_CHAT, ANOTHER_PUBLIC_CHAT)
    bot.set_chat_member_tag.side_effect = [TelegramAPIError(method=None, message="no"), True]

    await member_tagger.sync(player(), team())

    assert bot.set_chat_member_tag.await_count == 2
