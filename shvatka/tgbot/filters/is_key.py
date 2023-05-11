from aiogram.types import Message

from shvatka.core.utils.input_validation import normalize_key


def is_key(message: Message):
    if not message.text:
        return False
    key = normalize_key(message.text)
    return {"key": key} if key is not None else False
