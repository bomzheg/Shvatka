import importlib
import logging

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, ContentType
from aiogram.utils.markdown import html_decoration as hd
from opentelemetry import metrics

from shvatka.core.models import dto
from shvatka.core.services.chat import update_chat_id
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.views.commands import (
    CANCEL_COMMAND,
    CHAT_ID_COMMAND,
    ABOUT_COMMAND,
    CHAT_TYPE_COMMAND,
)

logger = logging.getLogger(__name__)
privacy_meter = metrics.get_meter("privacy.meter")
privacy_counter = privacy_meter.create_counter(
    name="privacy.got",
    description="how many times asked for privacy command",
    unit="count",
)


async def chat_id(message: Message, chat: dto.Chat, user: dto.User):
    text = f"id этого чата: {hd.pre(str(chat.tg_id))}\nВаш id: {hd.pre(user.tg_id)}"
    if message.reply_to_message and message.reply_to_message.from_user:
        text += (
            f"\nid {hd.bold(message.reply_to_message.from_user.full_name)}: "
            f"{hd.pre(message.reply_to_message.from_user.id)}"
        )
    await message.reply(text, disable_notification=True)


async def cancel_state(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    logger.info("Cancelling state %s", current_state)
    # Cancel state and inform user about it
    await state.clear()
    # And remove keyboard (just in case)
    await message.reply(
        "Диалог прекращён, данные удалены", reply_markup=ReplyKeyboardRemove(remove_keyboard=True)
    )


async def cmd_about(message: Message, user: dto.User, chat: dto.Chat):
    logger.info("User %s read about in %s", user.tg_id, chat.tg_id)
    await message.reply("Разработчик бота - @bomzheg\n")


async def chat_type_cmd_supergroup(message: Message):
    await message.reply(
        "Группа имеет тип supergroup, "
        "ты можешь создать команду в этом чате, отправив /create_team",
    )


async def chat_type_cmd_group(message: Message):
    await message.reply(
        "Группа имеет тип group, "
        "чтобы создать команду в этом чате - преобразуй группу в супергруппу"
        "https://telegra.ph/Preobrazovanie-gruppy-v-supergruppu-08-25",
    )


async def chat_migrate(message: Message, chat: dto.Chat, dao: HolderDao):
    new_id = message.migrate_to_chat_id
    await update_chat_id(chat, new_id, dao.chat)
    logger.info("Migrate chat from %s to %s", message.chat.id, new_id)


async def privacy(message: Message, user: dto.User):
    with (
        importlib.resources.path("shvatka.infrastructure.assets", "privacy.txt") as path,
        path.open("r") as f,
    ):
        await message.reply(f.read())
    privacy_counter.add(1, {"user": user.tg_id})


def setup() -> Router:
    router = Router(name=__name__)
    router.message.register(
        chat_id, Command(commands=["idchat", CHAT_ID_COMMAND.command], prefix="/!")
    )
    router.message.register(cmd_about, Command(commands=ABOUT_COMMAND))
    router.message.register(
        chat_type_cmd_group, Command(commands=CHAT_TYPE_COMMAND), F.chat.type == ChatType.GROUP
    )
    router.message.register(privacy, Command(commands=["privacy"]))
    router.message.register(
        chat_type_cmd_supergroup,
        Command(commands=CHAT_TYPE_COMMAND),
        F.chat.type == ChatType.SUPERGROUP,
    )
    router.message.register(
        cancel_state, Command(commands=CANCEL_COMMAND), F.chat.type != ChatType.PRIVATE
    )
    router.message.register(chat_migrate, F.content_types == ContentType.MIGRATE_TO_CHAT_ID)
    return router
