import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject, or_f
from aiogram.types import Message
from aiogram.utils.text_decorations import html_decoration as hd

from shvatka.core.models import dto
from shvatka.core.services.player import join_team, get_team_players
from shvatka.core.services.team import create_team
from shvatka.core.utils.defaults_constants import DEFAULT_ROLE
from shvatka.core.utils.exceptions import (
    TeamError,
    PlayerAlreadyInTeam,
    AnotherTeamInChat,
    PlayerRestoredInTeam,
    PermissionsError,
)
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import states
from shvatka.tgbot.filters.has_target import HasTargetFilter
from shvatka.tgbot.filters.is_admin import is_admin_filter
from shvatka.tgbot.filters.is_team import IsTeamFilter
from shvatka.tgbot.filters.team_player import TeamPlayerFilter
from shvatka.tgbot.middlewares import TeamPlayerMiddleware
from shvatka.tgbot.utils.router import disable_router_on_game, register_start_handler
from shvatka.tgbot.views.commands import (
    CREATE_TEAM_COMMAND,
    ADD_IN_TEAM_COMMAND,
    TEAM_COMMAND,
    PLAYERS_COMMAND,
    MANAGE_TEAM_COMMAND,
)
from shvatka.tgbot.views.team import render_team_card, render_team_players
from shvatka.tgbot.views.texts import NOT_SUPERGROUP_ERROR

logger = logging.getLogger(__name__)


async def cmd_create_team(
    message: Message,
    chat: dto.Chat,
    player: dto.Player,
    user: dto.User,
    dao: HolderDao,
    bot: Bot,
):
    logger.info("Player %s try create team in %s", player.id, chat.tg_id)
    if not await is_admin_filter(bot, chat, user):
        return await message.reply(
            "Создавать команду может только модератор",
        )

    chat.description = (await bot.get_chat(chat.tg_id)).description
    try:
        await create_team(chat, player, dao.team_creator)
    except PlayerAlreadyInTeam as e:
        return await message.reply(
            f"Вы уже находитесь в другой команде ({hd.quote(e.team.name)}).\n"  # type: ignore
            "Сперва нужно выйти из другой команды, и затем уже создавать собственную!"
        )
    except AnotherTeamInChat as e:
        return await message.reply(
            f"В этом чате уже создана команда ({hd.quote(e.team.name)}).\n"  # type: ignore
            "Создать другую команду можно только в другом чате!"
        )
    except TeamError as e:
        return await message.reply(
            "Несмотря на все наши проверки произошла какая-то ошибка при создании команды.\n"
            f"\n{e}",
            parse_mode=None,
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
    message: Message,
    team: dto.Team,
    target: dto.Player,
    player: dto.Player,
    bot: Bot,
    command: CommandObject,
    dao: HolderDao,
):
    logger.info(
        "Captain %s try to add %s in team %s",
        player.id,
        target.id,
        team.id,
    )
    try:
        chat_member = await bot.get_chat_member(team.get_chat_id(), target.get_chat_id())
    except TelegramBadRequest:
        return await message.reply("Не могу найти этого пользователя (его нет в чате?)")
    if chat_member.user.is_bot:
        return
    if chat_member.status == "left":
        return await message.reply("Не могу добавить этого пользователя. Вероятно его нет в чате")
    role = command.args or DEFAULT_ROLE
    try:
        await join_team(target, team, player, dao.team_player, role)
    except PlayerAlreadyInTeam as e:
        return await message.reply(
            f"Игрок {hd.quote(target.name_mention)} уже находится в команде "
            f"({hd.quote(e.team.name)}).\n"  # type: ignore
        )
    except PlayerRestoredInTeam:
        return await message.reply("Игрок возвращён в команду, я сделаю вид что и не покидал")
    except PermissionsError:
        return await message.reply(
            "У тебя нет прав добавлять игроков в команду. Обратись к капитану"
        )

    await message.answer(
        "В команду {team} добавлен игрок "
        "{player} в качестве роли указано: {role}".format(
            team=hd.bold(team.name), player=hd.bold(target.name_mention), role=hd.italic(role)
        )
    )
    logger.info(
        "Captain %s add to team %s player %s with role %s",
        player.id,
        team.id,
        target.id,
        role,
    )


async def cmd_team(message: Message, team: dto.Team):
    await message.answer(
        text=render_team_card(team),
        disable_web_page_preview=True,
    )


async def cmd_players(message: Message, team: dto.Team, dao: HolderDao):
    players = await get_team_players(team, dao.team_player)
    await message.answer(
        text=render_team_players(team=team, players=players, notification=False),
        disable_web_page_preview=True,
    )


def setup() -> Router:
    router = Router(name=__name__)
    router.message.outer_middleware.register(TeamPlayerMiddleware())
    disable_router_on_game(router)

    router.message.register(
        cmd_create_team,
        Command(commands=CREATE_TEAM_COMMAND.command),
        IsTeamFilter(is_team=False),
        F.chat.type == ChatType.SUPERGROUP,
    )
    router.message.register(
        cmd_create_team_group,
        Command(commands=CREATE_TEAM_COMMAND.command),
        F.chat.type == ChatType.GROUP,
    )
    router.message.register(
        cmd_add_in_team,
        Command(commands=ADD_IN_TEAM_COMMAND.command),
        HasTargetFilter(),
        IsTeamFilter(),
    )
    router.message.register(
        cmd_team,
        Command(commands=TEAM_COMMAND),
        IsTeamFilter(),
    )
    router.message.register(
        cmd_players,
        Command(commands=PLAYERS_COMMAND),
        IsTeamFilter(),
    )
    register_start_handler(
        Command(commands=MANAGE_TEAM_COMMAND),
        or_f(
            TeamPlayerFilter(is_captain=True),
            TeamPlayerFilter(can_manage_players=True),
            TeamPlayerFilter(can_remove_players=True),
            TeamPlayerFilter(can_change_team_name=True),
        ),
        state=states.CaptainsBridgeSG.main,
        router=router,
    )
    return router