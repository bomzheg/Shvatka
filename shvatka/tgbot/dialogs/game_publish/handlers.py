from datetime import datetime
from typing import Any

from aiogram import Bot
from aiogram.types import Message, ChatMemberAdministrator
from aiogram_dialog import DialogManager
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.interfaces.nursery import Nursery
from shvatka.core.services.game import get_full_game
from shvatka.core.services.game_stat import get_game_stat, get_typed_keys
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.tasks import publish_scenario_to_channel
from shvatka.tgbot.views.results.scenario import GamePublisher


@inject
async def process_publish_message(
    message: Message,
    dialog_: Any,
    manager: DialogManager,
    dao: FromDishka[HolderDao],
    idp: FromDishka[IdentityProvider],
    nursery: FromDishka[Nursery],
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

    data: dict[str, Any] = manager.start_data  # type: ignore[assignment]
    game_id: int = data["game_id"]
    game = await get_full_game(id_=game_id, identity=idp, dao=dao.game)
    game_stat = await get_game_stat(game=game, identity=idp, dao=dao.game_stat)
    keys = await get_typed_keys(game=game, identity=idp, dao=dao.typed_keys)
    approximate_time = GamePublisher.get_approximate_time_of(game)
    await message.answer(
        "Начинаю отправку сценария в канал, в связи с ограничениями платформы, "
        f"отправка займёт около {approximate_time.seconds // 60 + 1} мин. "
        "После завершения процесса, я сообщу. "
        "При желании можешь выйти из канала, "
        "после завершения я в любом случае пришлю ссылку для входа"
    )
    nursery.spawn(
        publish_scenario_to_channel,
        game=game,
        game_stat=game_stat,
        keys=keys,
        channel_id=channel_id,
        manager=manager.bg(),
    )
    await dao.game.set_published_channel_id(game, channel_id)
    await dao.commit()
    manager.dialog_data["started"] = True
    manager.dialog_data["started_at"] = datetime.now(tz=tz_utc).isoformat()
