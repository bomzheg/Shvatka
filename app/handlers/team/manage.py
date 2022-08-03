import logging

from aiogram import Bot, Dispatcher, F
from aiogram.dispatcher.filters import Command
from aiogram.types import Message
from aiogram.utils.text_decorations import html_decoration as hd

from app.dao.holder import HolderDao
from app.filters.is_admin import is_admin_filter
from app.models import dto
from app.services.team import create_team
from app.utils.exceptions import TeamError, GameStatusError, PlayerAlreadyInTeam, AnotherTeamInChat
from app.views.commands import CREATE_TEAM_COMMAND

logger = logging.getLogger(__name__)


# TODO все кнопки для редактирования команды останутся доступны для капитана если он сменил команду и снова капитан
#  другой команды
# TODO аналогично это может сработать для кнопок старой команды игрока с полномочиями
async def cmd_create_team(
    message: Message, chat: dto.Chat, player: dto.Player, dao: HolderDao,
    bot: Bot,
):
    logger.info(
        "User %s try create team in %s",
        message.from_user.id, message.chat.id
    )
    if not await is_admin_filter(bot, chat, player.user):
        return await message.reply(
            "Создавать команду может только модератор",
        )

    chat.description = (await bot.get_chat(chat.tg_id)).description
    try:
        await create_team(chat, player, dao)
    except PlayerAlreadyInTeam as e:
        return await message.reply(
            f"Вы уже находитесь в другой команде ({hd.quote(e.team.name)}).\n"
            "Сперва нужно выйти из другой команды, и затем уже создавать собственную!"
        )
    except AnotherTeamInChat as e:
        return await message.reply(
            f"В этом чате уже создана команда ({hd.quote(e.team.name)}).\n"
            "Создать другую команду можно только в другом чате!"
        )
    except TeamError as e:
        return await message.reply(
            "Несмотря на все наши проверки произошла какая-то ошибка при создании команды.\n"
            f"\n{e}",
            parse_mode=None
        )
    await message.reply(
        "Команда создана.\nДля просмотра информации о команде /team \n"
        "Для просмотра списка игроков /players\n"
        "Чтобы добавить игрока в команду - отправьте реплаем на его сообщение "
        "<b>/add_in_team [необязательно: роль в команде (водитель, полевой, мозг, итд)]</b>"
    )


def setup_team_manage(dp: Dispatcher):
    dp.message.register(
        cmd_create_team,
        Command(commands=CREATE_TEAM_COMMAND.command),
        GameStatusError(running=False),
        F.chat.type == "supergroup",
    )
