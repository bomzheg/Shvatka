import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import (
    Command,
    CommandObject,
    or_f,
    ChatMemberUpdatedFilter,
    IS_NOT_MEMBER,
    IS_MEMBER,
)
from aiogram.types import Message, ChatMemberUpdated, CallbackQuery, LinkPreviewOptions
from aiogram.utils.text_decorations import html_decoration as hd

from shvatka.core.models import dto
from shvatka.core.services.player import get_team_players, get_player_by_id, join_team
from shvatka.core.services.team import create_team
from shvatka.core.utils import exceptions
from shvatka.core.utils.defaults_constants import DEFAULT_ROLE
from shvatka.core.utils.exceptions import (
    TeamError,
    PlayerAlreadyInTeam,
    AnotherTeamInChat,
)
from shvatka.core.views.game import GameLogWriter
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import keyboards as kb
from shvatka.tgbot.filters.has_target import HasTargetFilter
from shvatka.tgbot.filters.is_admin import is_admin_filter
from shvatka.tgbot.filters.is_team import IsTeamFilter
from shvatka.tgbot.filters.team_player import TeamPlayerFilter
from shvatka.tgbot.middlewares import TeamPlayerMiddleware
from shvatka.tgbot.utils.router import disable_router_on_game
from shvatka.tgbot.views.commands import (
    CREATE_TEAM_COMMAND,
    ADD_IN_TEAM_COMMAND,
    TEAM_COMMAND,
    PLAYERS_COMMAND,
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
    game_log: GameLogWriter,
):
    logger.info("Player %s try create team in %s", player.id, chat.tg_id)
    if not await is_admin_filter(bot, chat, user):
        return await message.reply(
            "Создавать команду может только модератор",
        )

    chat.description = (await bot.get_chat(chat.tg_id)).description
    try:
        await create_team(chat, player, dao.team_creator, game_log)
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


async def user_join_chat_with_team(
    event: ChatMemberUpdated, team: dto.Team, player: dto.Player, bot: Bot
) -> None:
    await bot.send_message(
        chat_id=event.chat.id,
        text=f"Принять {hd.quote(player.name_mention)} в команду {hd.quote(team.name)}?",
        reply_markup=kb.get_join_team_kb(team, player),
    )


async def cmd_add_in_team(
    _: Message,
    team: dto.Team,
    target: dto.Player,
    player: dto.Player,
    bot: Bot,
    command: CommandObject,
    dao: HolderDao,
):
    role = command.args or DEFAULT_ROLE
    logger.info(
        "Captain %s try to add %s in team %s",
        player.id,
        target.id,
        team.id,
    )
    try:
        chat_member = await bot.get_chat_member(team.get_chat_id(), target.get_chat_id())
    except TelegramBadRequest:
        return await bot.send_message(
            chat_id=team.get_chat_id(), text="Не могу найти этого пользователя (его нет в чате?)"
        )
    if chat_member.user.is_bot:
        return
    if chat_member.status == "left":
        return await bot.send_message(
            chat_id=team.get_chat_id(),
            text="Не могу добавить этого пользователя. Вероятно его нет в чате",
        )
    try:
        await join_team(target, team, player, dao.team_player, role)
    except PlayerAlreadyInTeam as e:
        return await bot.send_message(
            chat_id=team.get_chat_id(),
            text=f"Игрок {hd.quote(target.name_mention)} уже находится в команде "
            f"({hd.quote(e.team.name)}).\n",  # type: ignore
        )
    except exceptions.PlayerRestoredInTeam:
        return await bot.send_message(
            chat_id=team.get_chat_id(),
            text="Игрок возвращён в команду, я сделаю вид что и не покидал",
        )
    except exceptions.PermissionsError:
        return await bot.send_message(
            chat_id=team.get_chat_id(),
            text="У тебя нет прав добавлять игроков в команду. Обратись к капитану",
        )

    await bot.send_message(
        chat_id=team.get_chat_id(),
        text="В команду {team} добавлен игрок {player} в качестве роли указано: {role}".format(
            team=hd.bold(team.name), player=hd.bold(target.name_mention), role=hd.italic(role)
        ),
    )


async def button_join(
    callback_query: CallbackQuery,
    callback_data: kb.JoinToTeamRequestCD,
    team: dto.Team,
    player: dto.Player,
    team_player: dto.TeamPlayer,
    bot: Bot,
    dao: HolderDao,
):
    if team.id != callback_data.team_id:
        raise exceptions.SHDataBreach(
            f"asked about team_id {callback_data.team_id} but in team {team.id}"
        )
    if team_player.team_id != team.id:
        return await callback_query.answer("Ты состоишь в другой команде!", show_alert=True)
    await callback_query.answer()
    target = await get_player_by_id(callback_data.player_id, dao.player)
    logger.info(
        "Captain %s try to add %s in team %s",
        player.id,
        target.id,
        team.id,
    )
    chat_member = await bot.get_chat_member(team.get_chat_id(), target.get_chat_id())
    if chat_member.user.is_bot:
        return
    if chat_member.status == "left":
        return await bot.send_message(
            chat_id=team.get_chat_id(),
            text="Не могу добавить этого пользователя. Вероятно его уже нет в чате",
        )
    assert callback_query.message
    try:
        await join_team(target, team, player, dao.team_player)
    except PlayerAlreadyInTeam as e:
        return await bot.edit_message_text(
            chat_id=team.get_chat_id(),
            message_id=callback_query.message.message_id,
            text=f"Игрок {hd.quote(target.name_mention)} уже находится в команде "
            f"({hd.quote(e.team.name)}).\n",  # type: ignore
        )
    except exceptions.PlayerRestoredInTeam:
        return await bot.edit_message_text(
            chat_id=team.get_chat_id(),
            message_id=callback_query.message.message_id,
            text="Игрок возвращён в команду, я сделаю вид что и не покидал",
        )
    except exceptions.PermissionsError:
        return await callback_query.answer(
            text="У тебя нет прав добавлять игроков в команду. Обратись к капитану",
            show_alert=True,
        )
    await bot.edit_message_text(
        chat_id=team.get_chat_id(),
        message_id=callback_query.message.message_id,
        text=f"В команду {hd.bold(team.name)} добавлен игрок {hd.bold(target.name_mention)}",
    )


async def button_join_no(
    callback_query: CallbackQuery,
    callback_data: kb.JoinToTeamRequestCD,
    team: dto.Team,
    player: dto.Player,
    team_player: dto.TeamPlayer,
    dao: HolderDao,
):
    if team.id != callback_data.team_id:
        raise exceptions.SHDataBreach(
            f"asked about team_id {callback_data.team_id} but in team {team.id}"
        )
    if team_player.team_id != team.id:
        return await callback_query.answer("Ты состоишь в другой команде!", show_alert=True)
    await callback_query.answer()
    target = await get_player_by_id(callback_data.player_id, dao.player)
    assert isinstance(callback_query.message, Message)
    await callback_query.message.edit_text(
        f"{hd.quote(player.name_mention)} не стал принимать "
        f"игрока {hd.quote(target.name_mention)} в команду"
    )


async def answer_not_enough_rights(callback_query: CallbackQuery):
    await callback_query.answer("Недостаточно прав", show_alert=True)


async def cmd_team(message: Message, team: dto.Team):
    await message.answer(
        text=render_team_card(team),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


async def cmd_players(message: Message, team: dto.Team, dao: HolderDao):
    players = await get_team_players(team, dao.team_player)
    await message.answer(
        text=render_team_players(team=team, players=players, notification=False),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


def setup() -> Router:
    router = Router(name=__name__)
    router.message.outer_middleware.register(TeamPlayerMiddleware())
    router.callback_query.outer_middleware.register(TeamPlayerMiddleware())
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
    router.chat_member.register(
        user_join_chat_with_team,
        ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER),
        IsTeamFilter(),
    )
    router.callback_query.register(
        button_join,
        kb.JoinToTeamRequestCD.filter(F.y_n),
        or_f(TeamPlayerFilter(is_captain=True), TeamPlayerFilter(can_add_players=True)),
        IsTeamFilter(),
    )
    router.callback_query.register(
        button_join_no,
        kb.JoinToTeamRequestCD.filter(~F.y_n),
        or_f(TeamPlayerFilter(is_captain=True), TeamPlayerFilter(can_add_players=True)),
        IsTeamFilter(),
    )
    router.callback_query.register(
        answer_not_enough_rights,
        kb.JoinToTeamRequestCD.filter(),
    )
    return router
