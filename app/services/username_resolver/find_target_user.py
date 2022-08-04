import logging

from aiogram.types import Message

from app.dao.holder import HolderDao
from app.models import dto
from app.utils.exceptions import MultipleUsernameFound, NoUsernameFound
from .user_getter import UserGetter

logger = logging.getLogger(__name__)


def get_target_user(message: Message, can_be_same=False, can_be_bot=False) -> dto.User | None:
    """
    Target user can take from reply or by mention
    :param message:
    :param can_be_same:
    :param can_be_bot:
    :return:
    """

    author_user = dto.User.from_aiogram(message.from_user)

    target_user = get_replied_user(message)
    if has_target_user(target_user, author_user, can_be_same, can_be_bot):
        return target_user

    target_user = get_mentioned_user(message)
    if has_target_user(target_user, author_user, can_be_same, can_be_bot):
        return target_user
    return None


def has_target_user(
    target_user: dto.User, author_user: dto.User, can_be_same: bool, can_be_bot: bool
) -> bool:
    """
    :return: True if target_user exist, not is author and not bot
    """
    if target_user is None:
        return False
    if not can_be_bot and target_user.is_bot:
        #   and not is_bot_username(target_user.username)
        # don't check is_bot_username because user can have username like @user_bot
        return False
    if not can_be_same and is_one_user(author_user, target_user):
        return False

    return True


def is_one_user(user_1: dto.User, user_2: dto.User) -> bool:
    if all([
        user_1.tg_id is not None,
        user_2.tg_id is not None,
        user_1.tg_id == user_2.tg_id,
    ]):
        return True
    if all([
        user_1.username is not None,
        user_2.username is not None,
        user_1.username == user_2.username,
    ]):
        return True

    return False


def get_mentioned_user(message: Message) -> dto.User | None:
    possible_mentioned_text = message.text or message.caption
    if not possible_mentioned_text:
        return None
    entities = message.entities or message.caption_entities
    if not entities:
        return None
    for ent in entities:
        if ent.type == "text_mention":
            return dto.User.from_aiogram(ent.user)
        elif ent.type == "mention":
            username = ent.extract(possible_mentioned_text).lstrip("@")
            return dto.User(username=username, tg_id=None)
    return None


def get_replied_user(message: Message) -> dto.User | None:
    if message.reply_to_message:
        return dto.User.from_aiogram(message.reply_to_message.from_user)
    return None


async def get_db_user_by_tg_user(
    target: dto.User, user_getter: UserGetter, dao: HolderDao,
) -> dto.User:
    if target.tg_id:
        return await dao.user.upsert_user(target)
    try:
        return await dao.user.get_by_username(target.username)
    except MultipleUsernameFound:
        logger.warning("Strange, multiple username? username=%s", target.username)
    except NoUsernameFound:
        logger.info("username not found in db %s", target.username)

    tg_user = await user_getter.get_user_by_username(target.username)

    return await dao.user.upsert_user(tg_user)
