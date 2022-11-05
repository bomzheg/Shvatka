from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import html_decoration as hd

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.models.enums import GameStatus
from shvatka.models.enums.played import Played
from shvatka.services.player import get_my_team, get_team_player
from shvatka.services.waiver import add_vote, approve_waivers, check_allow_approve_waivers, revoke_vote_by_captain, \
    get_not_played_team_players
from shvatka.utils.exceptions import PlayerNotInTeam, AnotherGameIsActive
from tgbot import keyboards as kb
from tgbot.filters.game_status import GameStatusFilter
from tgbot.filters.is_team import IsTeamFilter
from tgbot.services.waiver import swap_saved_message, get_saved_message
from tgbot.views.commands import START_WAIVERS_COMMAND, APPROVE_WAIVERS_COMMAND
from tgbot.views.utils import total_remove_msg
from tgbot.views.waiver import get_waiver_poll_text, start_approve_waivers, get_waiver_final_text


async def start_waivers(m: Message, team: dto.Team, game: dto.Game, dao: HolderDao, bot: Bot):
    msg = await m.answer(
        text=await get_waiver_poll_text(team, game, dao),
        reply_markup=kb.get_kb_waivers(team),
        disable_web_page_preview=True,
    )
    old_msg_id = await swap_saved_message(game, msg, dao.poll)
    await total_remove_msg(bot, m.chat.id, old_msg_id)


async def add_vote_handler(
    c: CallbackQuery,
    callback_data: kb.WaiverVoteCD,
    player: dto.Player,
    team: dto.Team,
    game: dto.Game,
    dao: HolderDao,
):
    if team.id != callback_data.team_id:
        raise PlayerNotInTeam(player=player, team=team)
    await add_vote(
        game=game, team=team, player=player, vote=callback_data.vote, dao=dao.waiver_vote_adder,
    )
    await c.answer()
    await c.message.edit_text(
        text=await get_waiver_poll_text(team, game, dao),
        reply_markup=kb.get_kb_waivers(team),
        disable_web_page_preview=True,
    )


async def start_approve_waivers_handler(
    m: Message,
    player: dto.Player,
    game: dto.Game,
    dao: HolderDao,
    bot: Bot
):
    team = await get_my_team(player, dao.player_in_team)
    check_allow_approve_waivers(await get_team_player(player, team, dao.waiver_approver))
    await total_remove_msg(
        bot=bot,
        chat_id=team.chat.tg_id,
        msg_id=await get_saved_message(game, team, dao.poll)
    )
    await bot.send_message(
        chat_id=player.user.tg_id,
        **await start_approve_waivers(game, team, dao),
    )


async def waiver_main_menu(
    c: CallbackQuery,
    callback_data: kb.WaiverMainCD,
    player: dto.Player,
    game: dto.Game,
    dao: HolderDao,
):
    if game.id != callback_data.game_id:
        raise AnotherGameIsActive(game=game, player=player)
    team = await get_my_team(player, dao.player_in_team)
    if team.id != callback_data.team_id:
        raise PlayerNotInTeam(
            player=player, team=team,
            notify_user="Ты не состоишь в команде, за которую подаёшь вейверы!",
        )
    check_allow_approve_waivers(await get_team_player(player, team, dao.waiver_approver))
    await c.message.edit_text(**await start_approve_waivers(game, team, dao))


async def confirm_approve_waivers_handler(
    c: CallbackQuery,
    callback_data: kb.WaiverConfirmCD,
    player: dto.Player,
    game: dto.Game,
    dao: HolderDao,
    bot: Bot,
):
    if game.id != callback_data.game_id:
        raise AnotherGameIsActive(game=game, player=player)
    team = await get_my_team(player, dao.player_in_team)
    if team.id != callback_data.team_id:
        raise PlayerNotInTeam(
            player=player, team=team,
            notify_user="Ты не состоишь в команде, за которую подаёшь вейверы!",
        )
    await approve_waivers(game=game, team=team, approver=player, dao=dao.waiver_approver)
    await bot.send_message(
        chat_id=team.chat.tg_id,
        text=await get_waiver_final_text(team, game, dao),
        disable_web_page_preview=True,
    )
    await c.answer("Вейверы успешно опубликованы!")


async def waiver_user_menu(
    c: CallbackQuery,
    callback_data: kb.WaiverManagePlayerCD,
    game: dto.Game,
    player: dto.Player,
    dao: HolderDao,
):
    if game.id != callback_data.game_id:
        raise AnotherGameIsActive(game=game, player=player)
    team = await get_my_team(player, dao.player_in_team)
    if team.id != callback_data.team_id:
        raise PlayerNotInTeam(
            player=player, team=team,
            notify_user="Ты не состоишь в команде, за которую подаёшь вейверы!",
        )

    await c.answer()
    await c.message.edit_text(
        text=f"Схватчик {hd.quote(player.user.name_mention)} команды {hd.quote(team.name)}"
             f"заявил что хочет участвовать в игре {hd.quote(game.name)}. Что хотите с ним делать?",
        reply_markup=kb.get_kb_waiver_one_player(team=team, player=player, game=game),
        disable_web_page_preview=True,
    )


async def waiver_remove_user_vote(
    c: CallbackQuery,
    callback_data: kb.WaiverRemovePlayerCD,
    player: dto.Player,
    game: dto.Game,
    dao: HolderDao,
):
    if game.id != callback_data.game_id:
        raise AnotherGameIsActive(game=game, player=player)
    team = await get_my_team(player, dao.player_in_team)
    if team.id != callback_data.team_id:
        raise PlayerNotInTeam(
            player=player, team=team,
            notify_user="Ты не состоишь в команде, за которую подаёшь вейверы!",
        )
    target = await dao.player.get_by_id(callback_data.player_id)
    await revoke_vote_by_captain(game, team, player, target, dao.waiver_approver)
    await c.answer()
    await c.message.edit_text(**await start_approve_waivers(game, team, dao))


async def waiver_add_force_menu(
    c: CallbackQuery,
    callback_data: kb.WaiverRemovePlayerCD,
    player: dto.Player,
    game: dto.Game,
    dao: HolderDao,
):
    if game.id != callback_data.game_id:
        raise AnotherGameIsActive(game=game, player=player)
    team = await get_my_team(player, dao.player_in_team)
    if team.id != callback_data.team_id:
        raise PlayerNotInTeam(
            player=player, team=team,
            notify_user="Ты не состоишь в команде, за которую подаёшь вейверы!",
        )
    check_allow_approve_waivers(await get_team_player(player, team, dao.waiver_approver))
    players = await get_not_played_team_players(team=team, dao=dao.waiver_approver)
    await c.answer()
    await c.message.edit_text(
        text="Кого из игроков добавить в список вейверов принудительно?",
        reply_markup=kb.get_kb_force_add_waivers(team, players, game),
        disable_web_page_preview=True,
    )


async def add_force_player(
    c: CallbackQuery,
    callback_data: kb.WaiverAddPlayerForceCD,
    player: dto.Player,
    game: dto.Game,
    dao: HolderDao,
):
    if game.id != callback_data.game_id:
        raise AnotherGameIsActive(game=game, player=player)
    team = await get_my_team(player, dao.player_in_team)
    if team.id != callback_data.team_id:
        raise PlayerNotInTeam(
            player=player, team=team,
            notify_user="Ты не состоишь в команде, за которую подаёшь вейверы!",
        )
    check_allow_approve_waivers(await get_team_player(player, team, dao.waiver_approver))
    target = await dao.player.get_by_id(callback_data.player_id)
    await add_vote(game, team, target, Played.yes, dao.waiver_vote_adder)
    players = await get_not_played_team_players(team=team, dao=dao.waiver_approver)
    await c.answer()
    await c.message.edit_text(
        text="Кого из игроков добавить в список вейверов принудительно?",
        reply_markup=kb.get_kb_force_add_waivers(team, players, game),
        disable_web_page_preview=True,
    )


def setup() -> Router:
    router = Router(name=__name__)
    # TODO добавить обработку событий ниже, сработавших не в тот статус
    router.message.filter(
        GameStatusFilter(status=GameStatus.getting_waivers),
    )
    router.callback_query.filter(
        GameStatusFilter(status=GameStatus.getting_waivers),
    )
    # TODO can_manage_waivers=True
    router.message.register(start_waivers, Command(START_WAIVERS_COMMAND), IsTeamFilter())
    # TODO is_team_player
    router.callback_query.register(add_vote_handler, kb.WaiverVoteCD.filter(), IsTeamFilter())
    #  TODO can_manage_waivers=True
    router.message.register(start_approve_waivers_handler, Command(APPROVE_WAIVERS_COMMAND))
    router.callback_query.register(confirm_approve_waivers_handler, kb.WaiverConfirmCD.filter())

    router.callback_query.register(waiver_user_menu, kb.WaiverManagePlayerCD.filter())
    router.callback_query.register(waiver_remove_user_vote, kb.WaiverRemovePlayerCD.filter())
    router.callback_query.register(waiver_add_force_menu, kb.WaiverAddForceMenuCD.filter())
    router.callback_query.register(add_force_player, kb.WaiverAddPlayerForceCD.filter())
    return router
