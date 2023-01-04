from aiogram.types import Message

from shvatka.utils.input_validation import normalize_key


def is_key(message: Message):
    assert isinstance(message.text, str)
    key = normalize_key(message.text)
    return {"key": key} if key is not None else False
