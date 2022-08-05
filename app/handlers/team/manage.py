import logging

from aiogram import Bot, Dispatcher, F
from aiogram.dispatcher.filters import Command, CommandObject
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from aiogram.utils.text_decorations import html_decoration as hd

from app.dao.holder import HolderDao
from app.filters.game_status import GameStatusFilter
from app.filters.has_target import HasTargetFilter
from app.filters.is_admin import is_admin_filter
from app.filters.is_team import IsTeamFilter
from app.models import dto
from app.services.player import add_player_in_team
from app.services.team import create_team
from app.utils.defaults_constants import DEFAULT_ROLE
from app.utils.exceptions import TeamError, PlayerAlreadyInTeam, AnotherTeamInChat, PlayerRestoredInTeam
from app.views.commands import CREATE_TEAM_COMMAND, ADD_IN_TEAM_COMMAND
from app.views.texts import NOT_SUPERGROUP_ERROR

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


async def cmd_create_team_group(message: Message, user: dto.User, chat: dto.Chat):
    logger.info("User %s try create team in GROUP %s", user.tg_id, chat.tg_id)
    await message.reply(NOT_SUPERGROUP_ERROR)


async def cmd_add_in_team(
    message: Message, team: dto.Team, target: dto.Player, bot: Bot,
    command: CommandObject, dao: HolderDao,
):
    logger.info(
        "Captain %s try to add %s in team %s",
        message.from_user.id, target.user.tg_id, team.id,
    )
    try:
        chat_member = await bot.get_chat_member(team.chat.tg_id, target.user.tg_id)
    except TelegramBadRequest:
        return await message.reply("Не могу найти этого пользователя (его нет в чате?)")
    if chat_member.user.is_bot:
        return
    if chat_member.status == "left":
        return await message.reply(
            "Не могу добавить этого пользователя. Вероятно его нет в чате"
        )
    role = command.args or DEFAULT_ROLE
    try:
        await add_player_in_team(target, team, dao.player_in_team, role)
    except PlayerAlreadyInTeam as e:
        return await message.reply(
            f"Игрок {hd.quote(target.user.fullname)} уже находится в команде "
            f"({hd.quote(e.team.name)}).\n"
        )
    except PlayerRestoredInTeam:
        return await message.reply(
            "Игрок возвращён в команду, я сделаю вид что и не покидал"
        )
    await message.answer(
        "В команду {team} добавлен игрок "
        "{player} в качестве роли указано: {role}"
        .format(
            team=hd.bold(team.name),
            player=hd.bold(target.user.name_mention),
            role=hd.italic(role)
        )
    )
    logger.info(
        "Captain %s add to team %s player %s with role %s",
        message.from_user.id, team.id, target.user.tg_id, role,
    )


def setup_team_manage(dp: Dispatcher):
    dp.message.register(
        cmd_create_team,
        Command(commands=CREATE_TEAM_COMMAND.command),
        GameStatusFilter(running=False),
        F.chat.type == "supergroup",
    )
    dp.message.register(
        cmd_create_team_group,
        Command(commands=CREATE_TEAM_COMMAND.command),
        GameStatusFilter(running=False),
        F.chat.type == "group",
    )
    dp.message.register(
        cmd_add_in_team,
        Command(commands=ADD_IN_TEAM_COMMAND.command),
        GameStatusFilter(running=False),
        HasTargetFilter(),
        IsTeamFilter(),
        # can_add_player=True
    )
