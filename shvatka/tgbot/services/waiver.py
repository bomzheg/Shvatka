from aiogram.types import Message

from shvatka.core.models import dto
from shvatka.infrastructure.db.dao import PollDao


async def swap_saved_message(game: dto.Game, msg: Message, dao: PollDao):
    old_msg_id = await dao.get_poll_msg_id(chat_id=msg.chat.id, game_id=game.id)
    await dao.save_poll_msg_id(chat_id=msg.chat.id, game_id=game.id, msg_id=msg.message_id)
    return old_msg_id


async def get_saved_message(game: dto.Game, team: dto.Team, dao: PollDao) -> int | None:
    chat_id = team.get_chat_id()
    assert chat_id is not None
    return await dao.get_poll_msg_id(chat_id=chat_id, game_id=game.id)
