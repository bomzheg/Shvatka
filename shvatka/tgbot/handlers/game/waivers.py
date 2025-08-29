from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, LinkPreviewOptions
from dishka import FromDishka
from dishka.integrations.aiogram import inject

from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.waiver.interactors import (
    WaiverCompleteReaderInteractor,
    WaiverDraftReaderInteractor,
)
from shvatka.tgbot.filters import GameStatusFilter
from shvatka.tgbot.services.identity import TgBotIdentityProvider
from shvatka.tgbot.views.commands import GET_WAIVERS_COMMAND, GET_WAIVERS_DRAFT_COMMAND
from shvatka.tgbot.views.waiver import render_all_teams_waivers, render_all_teams_poll_stat


@inject
async def get_waivers_cmd(
    m: Message,
    current_game: FromDishka[CurrentGameProvider],
    interactor: FromDishka[WaiverCompleteReaderInteractor],
):
    game = await current_game.get_required_game()
    votes = await interactor(game=game)
    await m.answer(
        text=render_all_teams_waivers(votes) or "Пока ещё никто не сдал вейверы",
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


@inject
async def get_waivers_draft_cmd(
    m: Message,
    identity_provider: FromDishka[TgBotIdentityProvider],
    interactor: FromDishka[WaiverDraftReaderInteractor],
):
    data = await interactor(identity=identity_provider)
    await m.answer(
        text=render_all_teams_poll_stat(data) or "Пока ещё никто не голосовал",
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


def setup() -> Router:
    router = Router(name=__name__)
    router.message.filter(
        GameStatusFilter(active=True),
    )
    router.callback_query.filter(
        GameStatusFilter(active=True),
    )
    router.message.register(get_waivers_cmd, Command(GET_WAIVERS_COMMAND))
    router.message.register(get_waivers_draft_cmd, Command(GET_WAIVERS_DRAFT_COMMAND))
    return router
