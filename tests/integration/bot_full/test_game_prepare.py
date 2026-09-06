import typing
from collections.abc import Iterable
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from aiogram.client.session.base import BaseSession
from dishka import AsyncContainer

from shvatka.core.models import dto
from shvatka.core.models.enums import GameStatus
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.tgbot.services.bot_rights import ChatRights
from shvatka.tgbot.views.game import BotView
from shvatka.tgbot.views.pinner import MessagePinner, PinCategory
from tests.integration.bot_full.test_pinner import message

CAN_PIN = ChatRights(can_pin_messages=True, can_manage_tags=False)
POLL_MESSAGE_ID = 100500


class PollPreparer:
    """Preparing a view only asks the dao for the waivers poll message."""

    async def get_poll_msg(self, team: dto.Team, game: dto.Game) -> int | None:
        return POLL_MESSAGE_ID

    async def get_agree_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        raise NotImplementedError

    async def get_orgs(
        self, game: dto.Game, with_deleted: bool = False
    ) -> list[dto.SecondaryOrganizer]:
        raise NotImplementedError

    async def delete_poll_data(self) -> None:
        raise NotImplementedError


def api_methods(bot_session: BaseSession) -> list[str]:
    session = typing.cast(MagicMock, bot_session)
    return [
        method
        for call in session.mock_calls
        if len(call.args) > 1
        and (method := getattr(call.args[1], "__api_method__", None)) is not None
    ]


def prepared_game(author: dto.Player) -> dto.Game:
    return dto.Game(
        id=1,
        author=author,
        name="Кубок огня",
        status=GameStatus.getting_waivers,
        manage_token="token",
        start_at=datetime.now(tz=tz_utc) + timedelta(minutes=5),
        number=None,
        results=dto.GameResults(
            published_chanel_id=None, results_picture_file_id=None, keys_url=None
        ),
    )


@pytest.mark.asyncio
async def test_prepare_sends_before_unpinning(
    harry: dto.Player,
    gryffindor: dto.Team,
    dishka_request: AsyncContainer,
    bot_session: BaseSession,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(MessagePinner, "SLEEP", timedelta(0))
    view = await dishka_request.get(BotView)
    chat_id = gryffindor.get_chat_id()
    assert chat_id is not None
    # rights are cached, so the pinner doesn't ask telegram about them
    view.pinner.rights.save(chat_id, CAN_PIN)
    # a previous game was finished abnormally and left a pinned message
    await view.pinner.pin(chat_id, [message(1)], PinCategory.level)
    typing.cast(MagicMock, bot_session).reset_mock()

    await view.prepare_game_view(
        game=prepared_game(harry), teams=[gryffindor], orgs=[], dao=PollPreparer()
    )

    # the prepare message comes first: a flood limit must be spent on it,
    # not on cleaning up the pins of the previous game
    assert ["sendMessage", "editMessageReplyMarkup", "unpinChatMessage"] == api_methods(
        bot_session
    )
