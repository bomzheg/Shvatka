import logging
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import AiogramError
from aiogram.utils.text_decorations import html_decoration as hd

from shvatka.core.models.enums.request import RequestType
from shvatka.core.notifications import dto as ndto
from shvatka.core.notifications.adapters import RequestNotifier, RequestStorage
from shvatka.core.interfaces.dal.player import PlayerByIdGetter, TeamPlayersGetter
from shvatka.core.interfaces.dal.team import TeamByIdGetter
from shvatka.tgbot.keyboards.action_request import get_action_request_kb

logger = logging.getLogger(__name__)

MERGE_REQUEST_TYPES = (RequestType.team_merge, RequestType.player_merge)


@dataclass
class BotRequestNotifier(RequestNotifier):
    bot: Bot
    requests: RequestStorage
    player_dao: PlayerByIdGetter
    team_dao: TeamByIdGetter
    team_players_dao: TeamPlayersGetter
    game_log_chat: int

    async def notify_created(self, request: ndto.ActionRequest) -> None:
        for chat_id in await self._chat_ids(request):
            try:
                message = await self.bot.send_message(
                    chat_id=chat_id,
                    text=self._render(request),
                    reply_markup=get_action_request_kb(request.id),
                    disable_notification=False,
                )
            except AiogramError as e:
                logger.warning(
                    "failed to send action request %s to %s", request.id, chat_id, exc_info=e
                )
                continue
            await self.requests.add_bot_message(
                request.id, chat_id=message.chat.id, message_id=message.message_id
            )

    async def _chat_ids(self, request: ndto.ActionRequest) -> list[int]:
        if request.type in MERGE_REQUEST_TYPES:
            # merge requests are answered by admins in the game-log channel
            return [self.game_log_chat]
        chat_ids = []
        for player_id in await self._recipient_ids(request):
            player = await self.player_dao.get_by_id(player_id)
            chat_id = player.get_chat_id()
            if chat_id is not None:
                chat_ids.append(chat_id)
        return chat_ids

    async def _recipient_ids(self, request: ndto.ActionRequest) -> set[int]:
        if request.target_player_id is not None:
            return {request.target_player_id}
        if request.type == RequestType.team_join_request and request.team_id is not None:
            # A join request is answerable by every manager, so bot delivery fans out to all
            # managers and stores every message for web-side cleanup.
            team = await self.team_dao.get_by_id(request.team_id)
            players = await self.team_players_dao.get_players(team)
            return {tp.player.id for tp in players if tp.is_captain or tp.can_add_players}
        return set()

    def _render(self, request: ndto.ActionRequest) -> str:
        payload = request.payload
        match request.type:
            case RequestType.team_join_invite:
                return (
                    f"{payload.get('inviter_name', 'Игрок')} приглашает вас в команду "
                    f"{payload.get('team_name', '')}."
                )
            case RequestType.team_join_request:
                return (
                    f"{payload.get('player_name', 'Игрок')} просит принять его в команду "
                    f"{payload.get('team_name', '')}."
                )
            case RequestType.org_invite:
                author_name = payload.get("author_name", "Автор")
                game_name = payload.get("game_name", "")
                return f"{author_name} приглашает вас стать организатором игры {game_name}."
            case RequestType.team_merge:
                return (
                    f"Капитан {hd.quote(payload.get('captain_name', ''))} "
                    f"предлагает объединить свою команду "
                    f"{hd.quote(payload.get('primary_team_name', ''))} "
                    f"с форумной версией {hd.quote(payload.get('secondary_team_name', ''))}"
                )
            case RequestType.player_merge:
                return (
                    f"Игрок {hd.quote(payload.get('initiator_name', ''))} "
                    f"предлагает объединить достижения игрока "
                    f"{hd.quote(payload.get('primary_player_name', ''))} "
                    f"с форумной версией {hd.quote(payload.get('secondary_player_name', ''))}"
                )
        return "Новый запрос"
