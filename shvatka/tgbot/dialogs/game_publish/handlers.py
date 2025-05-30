import asyncio
from datetime import datetime
from typing import Any

from aiogram import Bot
from aiogram.types import Message, ChatMemberAdministrator
from aiogram.utils.text_decorations import html_decoration as hd
from aiogram_dialog import DialogManager, BaseDialogManager
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject
from telegraph.aio import Telegraph

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.services.game import get_full_game
from shvatka.core.services.game_stat import get_typed_keys, get_game_stat
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.views.hint_sender import HintSender
from shvatka.tgbot.views.results.scenario import GamePublisher


@inject
async def process_publish_message(
    message: Message,
    dialog_: Any,
    manager: DialogManager,
    dao: FromDishka[HolderDao],
    telegraph: FromDishka[Telegraph],
    idp: FromDishka[IdentityProvider],
    hint_sender: FromDishka[HintSender],
):
    if not message.forward_from_chat or message.forward_from_chat.type != "channel":
        return await message.reply("Это не пересланное из канала сообщение.")
    channel_id = message.forward_from_chat.id
    bot: Bot = manager.middleware_data["bot"]
    admins = await bot.get_chat_administrators(channel_id)
    bot_admin = None
    for admin in admins:
        if admin.user.id == bot.id:
            bot_admin = admin
            break
    if bot_admin is None or not isinstance(bot_admin, ChatMemberAdministrator):
        return await message.answer("Я не админ в том канале.")
    if not bot_admin.can_post_messages:
        return await message.answer("У меня нет прав на отправку сообщений в том канале")
    if not bot_admin.can_invite_users:
        return await message.answer(
            "У меня нет права управлять пригласительными ссылками в том канале"
        )

    game_id = manager.start_data["game_id"]
    config: BotConfig = manager.middleware_data["config"]
    game = await get_full_game(id_=game_id, identity=idp, dao=dao.game)
    game_stat = await get_game_stat(game=game, identity=idp, dao=dao.game_stat)
    keys = await get_typed_keys(game=game, identity=idp, dao=dao.typed_keys)
    game_publisher = GamePublisher(
        hint_sender=hint_sender,
        game=game,
        channel_id=channel_id,
        bot=bot,
        config=config,
        game_stat=game_stat,
        keys=keys,
        telegraph=telegraph,
    )
    await message.answer(
        "Начинаю отправку сценария в канал, в связи с ограничениями платформы, "
        f"отправка займёт около {game_publisher.get_approximate_time().seconds // 60 + 1} мин. "
        "После завершения процесса, я сообщу. "
        "При желании можешь выйти из канала, "
        "после завершения я в любом случае пришлю ссылку для входа"
    )
    asyncio.create_task(publish_game(game_publisher, manager.bg()))
    await dao.game.set_published_channel_id(game, channel_id)
    await dao.commit()
    manager.dialog_data["started"] = True
    manager.dialog_data["started_at"] = datetime.now(tz=tz_utc).isoformat()


async def publish_game(game_publisher: GamePublisher, manager: BaseDialogManager):
    started_msg_id = await game_publisher.publish_scn()
    results_msg_id = await game_publisher.publish_results()
    keys_msg_id = await game_publisher.publish_keys()
    channel_id = game_publisher.channel_id
    bot = game_publisher.bot
    table_of_content = (
        f"Начало сценария: {no_public_message_link(channel_id, started_msg_id)}\n"
        f"Результаты игры: {no_public_message_link(channel_id, results_msg_id)}\n"
        f"Лог ключей: {no_public_message_link(channel_id, keys_msg_id)}"
    )
    await bot.send_message(chat_id=channel_id, text=table_of_content)
    invite = await get_invite(channel_id=channel_id, bot=bot)

    text_invite_scn = f"Чтобы его увидеть, нужно войти в канал: {invite}"
    await bot.send_message(
        game_publisher.config.game_log_chat,
        f"Загружен сценарий игры {hd.bold(hd.quote(game_publisher.game.name))}."
        f"\n{text_invite_scn}",
    )
    await manager.update(
        {"text_invite": text_invite_scn + "\n" + table_of_content, "started": False}
    )
    await bot.send_message(
        chat_id=game_publisher.game.author.get_chat_id(),  # type: ignore[arg-type]
        text=f"Сценарий загружен.\n{text_invite_scn}",
    )


async def get_invite(channel_id: int, bot: Bot) -> str:
    channel = await bot.get_chat(channel_id)
    invite = channel.invite_link
    if not invite:
        invite = await bot.export_chat_invite_link(channel_id)

    return invite


def no_public_message_link(chat_id: int, message_id: int):
    return f"https://t.me/c/{str(chat_id)[4:]}/{message_id}"
