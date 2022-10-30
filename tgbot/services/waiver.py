from aiogram.types import Message

from db.dao import PollDao
from shvatka.models import dto


async def swap_saved_message(game: dto.Game, msg: Message, dao: PollDao):
    old_msg_id = await dao.get_pool_msg_id(chat_id=msg.chat.id, game_id=game.id)
    await dao.save_pool_msg_id(chat_id=msg.chat.id, game_id=game.id, msg_id=msg.message_id)
    return old_msg_id
