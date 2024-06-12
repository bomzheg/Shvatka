from aiogram import Router, Bot, F
from aiogram.enums import ChatType
from aiogram.filters import Command, or_f
from aiogram.types import Message, CallbackQuery, LinkPreviewOptions
from aiogram.utils.markdown import html_decoration as hd

from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.core.models import dto
from shvatka.core.models.enums import GameStatus
from shvatka.core.models.enums.played import Played
from shvatka.core.services.player import get_my_team, get_full_team_player
from shvatka.core.services.waiver import (
    add_vote,
    approve_waivers,
    check_allow_approve_waivers,
    revoke_vote_by_captain,
    get_not_played_team_players,
    force_add_vote,
)
from shvatka.core.utils.exceptions import PlayerNotInTeam, AnotherGameIsActive
from shvatka.tgbot import keyboards as kb
from shvatka.tgbot.filters.game_status import GameStatusFilter
from shvatka.tgbot.filters.is_team import IsTeamFilter
from shvatka.tgbot.filters.team_player import TeamPlayerFilter
from shvatka.tgbot.middlewares import TeamPlayerMiddleware
from shvatka.tgbot.services.waiver import swap_saved_message, get_saved_message
from shvatka.tgbot.utils.router import disable_router_on_game
from shvatka.tgbot.views.commands import START_WAIVERS_COMMAND, APPROVE_WAIVERS_COMMAND
from shvatka.tgbot.views.utils import total_remove_msg
from shvatka.tgbot.views.waiver import (
    get_waiver_poll_text,
    start_approve_waivers,
    get_waiver_final_text,
)


async def start_waivers(
    message: Message, team: dto.Team | None, game: dto.Game, dao: HolderDao, bot: Bot
):
    if not team:
        await message.answer("Ты не в команде или не капитан")
        return
    msg = await bot.send_message(
        chat_id=team.get_chat_id(),
        text=await get_waiver_poll_text(team, game, dao),
        reply_markup=kb.get_kb_waivers(team, game),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )
    old_msg_id = await swap_saved_message(game, msg, dao.poll)
    await total_remove_msg(bot, team.get_chat_id(), old_msg_id)


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
        game=game,
        team=team,
        player=player,
        vote=callback_data.vote,
        dao=dao.waiver_vote_adder,
    )
    await c.answer()
    await c.message.edit_text(  # type: ignore[union-attr]
        text=await get_waiver_poll_text(team, game, dao),
        reply_markup=kb.get_kb_waivers(team, game),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


async def start_approve_waivers_cmd_handler(
    _: Message, player: dto.Player, user: dto.User, game: dto.Game, dao: HolderDao, bot: Bot
):
    team = await get_my_team(player, dao.team_player)
    check_allow_approve_waivers(await get_full_team_player(player, team, dao.waiver_approver))
    assert team is not None
    await total_remove_msg(
        bot=bot, chat_id=team.get_chat_id(), msg_id=await get_saved_message(game, team, dao.poll)
    )
    await bot.send_message(
        chat_id=user.tg_id,
        **await start_approve_waivers(game, team, dao),
    )


async def start_approve_waivers_cb_handler(
    c: CallbackQuery,
    callback_data: kb.WaiverToApproveCD,
    player: dto.Player,
    user: dto.User,
    game: dto.Game,
    dao: HolderDao,
    bot: Bot,
):
    check_same_game(callback_data, game, player)
    team = await get_my_team(player, dao.team_player)
    check_same_team(callback_data, player, team)
    assert team
    check_allow_approve_waivers(await get_full_team_player(player, team, dao.waiver_approver))
    await c.answer("Бот написал в ЛС")
    await total_remove_msg(
        bot=bot, chat_id=team.get_chat_id(), msg_id=await get_saved_message(game, team, dao.poll)
    )
    await bot.send_message(
        chat_id=user.tg_id,
        **await start_approve_waivers(game, team, dao),
    )


async def waiver_main_menu(
    c: CallbackQuery,
    callback_data: kb.WaiverMainCD,
    player: dto.Player,
    game: dto.Game,
    dao: HolderDao,
):
    check_same_game(callback_data, game, player)
    team = await get_my_team(player, dao.team_player)
    check_same_team(callback_data, player, team)
    check_allow_approve_waivers(await get_full_team_player(player, team, dao.waiver_approver))
    await c.message.edit_text(  # type: ignore[union-attr]
        **await start_approve_waivers(game, team, dao)
    )


async def confirm_approve_waivers_handler(
    c: CallbackQuery,
    callback_data: kb.WaiverConfirmCD,
    player: dto.Player,
    game: dto.Game,
    dao: HolderDao,
    bot: Bot,
):
    check_same_game(callback_data, game, player)
    team = await get_my_team(player, dao.team_player)
    check_same_team(callback_data, player, team)
    assert team
    await approve_waivers(game=game, team=team, approver=player, dao=dao.waiver_approver)
    await bot.send_message(
        chat_id=team.get_chat_id(),
        text=await get_waiver_final_text(team, game, dao),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )
    await c.answer("Вейверы успешно опубликованы!")
    assert c.message
    await total_remove_msg(bot, chat_id=c.message.chat.id, msg_id=c.message.message_id)


async def waiver_user_menu(
    c: CallbackQuery,
    callback_data: kb.WaiverManagePlayerCD,
    game: dto.Game,
    player: dto.Player,
    dao: HolderDao,
):
    check_same_game(callback_data, game, player)
    team = await get_my_team(player, dao.team_player)
    check_same_team(callback_data, player, team)
    assert team

    subject_player = await dao.player.get_by_id(callback_data.player_id)
    await c.answer()
    await c.message.edit_text(  # type: ignore[union-attr]
        text=f"Схватчик {hd.quote(subject_player.name_mention)} команды {hd.quote(team.name)} "
        f"заявил что хочет участвовать в игре {hd.quote(game.name)}. Что хотите с ним делать?",
        reply_markup=kb.get_kb_waiver_one_player(team=team, player=subject_player, game=game),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


async def waiver_remove_user_vote(
    c: CallbackQuery,
    callback_data: kb.WaiverRemovePlayerCD,
    player: dto.Player,
    game: dto.Game,
    dao: HolderDao,
):
    check_same_game(callback_data, game, player)
    team = await get_my_team(player, dao.team_player)
    check_same_team(callback_data, player, team)
    target = await dao.player.get_by_id(callback_data.player_id)
    await revoke_vote_by_captain(game, team, player, target, dao.waiver_approver)
    await c.answer()
    await c.message.edit_text(  # type: ignore[union-attr]
        **await start_approve_waivers(game, team, dao)
    )


async def waiver_add_force_menu(
    c: CallbackQuery,
    callback_data: kb.WaiverRemovePlayerCD,
    player: dto.Player,
    game: dto.Game,
    dao: HolderDao,
):
    check_same_game(callback_data, game, player)
    team = await get_my_team(player, dao.team_player)
    check_same_team(callback_data, player, team)
    check_allow_approve_waivers(await get_full_team_player(player, team, dao.waiver_approver))
    players = await get_not_played_team_players(team=team, dao=dao.waiver_approver)
    await c.answer()
    await c.message.edit_text(  # type: ignore[union-attr]
        text="Кого из игроков добавить в список вейверов принудительно?",
        reply_markup=kb.get_kb_force_add_waivers(team, players, game),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


async def add_force_player(
    c: CallbackQuery,
    callback_data: kb.WaiverAddPlayerForceCD,
    player: dto.Player,
    game: dto.Game,
    dao: HolderDao,
):
    check_same_game(callback_data, game, player)
    team = await get_my_team(player, dao.team_player)
    check_same_team(callback_data, player, team)
    check_allow_approve_waivers(await get_full_team_player(player, team, dao.waiver_approver))
    target = await dao.player.get_by_id(callback_data.player_id)
    await force_add_vote(game, team, target, Played.yes, dao.waiver_vote_adder)
    players = await get_not_played_team_players(team=team, dao=dao.waiver_approver)
    await c.answer()
    await c.message.edit_text(  # type: ignore[union-attr]
        text="Кого из игроков добавить в список вейверов принудительно?",
        reply_markup=kb.get_kb_force_add_waivers(team, players, game),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


async def player_is_not_captain(c: CallbackQuery):
    await c.answer("Недостаточно прав", show_alert=True, cache_time=10)


async def player_not_in_team_handler(c: CallbackQuery):
    await c.answer("Вы не состоите в этой команде", show_alert=True, cache_time=10)


def check_same_team(callback_data: kb.IWaiverCD, player: dto.Player, team: dto.Team) -> None:
    if not team or team.id != callback_data.team_id:
        raise PlayerNotInTeam(
            player=player,
            team=team,
            notify_user="Ты не состоишь в команде, за которую подаёшь вейверы!",
        )


def check_same_game(callback_data: kb.IWaiverCD, game: dto.Game, player: dto.Player) -> None:
    if game.id != callback_data.game_id:
        raise AnotherGameIsActive(game=game, player=player)


def setup() -> Router:
    router = Router(name=__name__)
    disable_router_on_game(router)

    captain_router = router.include_router(Router(name=__name__ + ".captain"))
    player_router = router.include_router(Router(name=__name__ + ".player"))
    fallback_router = router.include_router(Router(name=__name__ + ".fallback"))

    # filters
    router.message.filter(
        GameStatusFilter(status=GameStatus.getting_waivers),
    )
    router.callback_query.filter(
        GameStatusFilter(status=GameStatus.getting_waivers),
    )
    player_router.callback_query.filter(TeamPlayerFilter())
    captain_router.callback_query.filter(TeamPlayerFilter(can_manage_waivers=True))
    # middlewares
    player_router.callback_query.outer_middleware.register(TeamPlayerMiddleware())
    captain_router.message.outer_middleware.register(TeamPlayerMiddleware())
    captain_router.callback_query.outer_middleware.register(TeamPlayerMiddleware())

    # handlers
    captain_router.message.register(
        start_waivers,
        Command(START_WAIVERS_COMMAND),
        or_f(IsTeamFilter(), F.chat.type == ChatType.PRIVATE),
    )
    player_router.callback_query.register(
        add_vote_handler,
        kb.WaiverVoteCD.filter(),
        IsTeamFilter(),
    )
    captain_router.message.register(
        start_approve_waivers_cmd_handler,
        Command(APPROVE_WAIVERS_COMMAND),
    )
    captain_router.callback_query.register(
        start_approve_waivers_cb_handler,
        kb.WaiverToApproveCD.filter(),
    )
    player_router.callback_query.register(
        player_is_not_captain,
        kb.WaiverToApproveCD.filter(),
    )
    fallback_router.callback_query.register(
        player_is_not_captain,
        kb.WaiverToApproveCD.filter(),
    )
    captain_router.callback_query.register(
        confirm_approve_waivers_handler,
        kb.WaiverConfirmCD.filter(),
    )
    player_router.callback_query.register(
        player_is_not_captain,
        kb.WaiverConfirmCD.filter(),
    )
    fallback_router.callback_query.register(
        player_is_not_captain,
        kb.WaiverConfirmCD.filter(),
    )

    captain_router.callback_query.register(
        waiver_user_menu,
        kb.WaiverManagePlayerCD.filter(),
    )
    captain_router.callback_query.register(
        waiver_main_menu,
        kb.WaiverMainCD.filter(),
    )
    captain_router.callback_query.register(
        waiver_remove_user_vote,
        kb.WaiverRemovePlayerCD.filter(),
    )
    captain_router.callback_query.register(
        waiver_add_force_menu,
        kb.WaiverAddForceMenuCD.filter(),
    )
    captain_router.callback_query.register(
        add_force_player,
        kb.WaiverAddPlayerForceCD.filter(),
    )
    fallback_router.callback_query.register(
        player_not_in_team_handler,
        kb.WaiverVoteCD.filter(),
    )
    # TODO добавить обработку событий ниже, сработавших не в тот статус
    return router
