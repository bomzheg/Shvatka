import enum
from datetime import datetime

from aiogram.utils.text_decorations import html_decoration as hd

from shvatka.models import dto
from shvatka.utils.datetime_utils import tz_game, DATETIME_FORMAT


class KeyEmoji(enum.Enum):
    correct = "✅"
    incorrect = "❌"
    duplicate = "💤"


def render_log_keys(log_keys: dict[dto.Team, list[dto.KeyTime]]) -> str:
    text = f"Лог ключей на {datetime.now(tz=tz_game).strftime(DATETIME_FORMAT)}:<br/>"
    for team, keys in log_keys.items():
        text += f"<hr/>{hd.quote(team.name)}:"
        n_level = keys[0].level_number - 1
        for i, key in enumerate(keys):
            if n_level < key.level_number:
                # keys are sorted, so is previous and next level not equals - add caption
                n_level = key.level_number
                if i > 0:
                    text += "</ol><br/>"
                text += f"Уровень №{n_level + 1}<br/><ol>"
            text += (
                f"<li>{to_emoji(key).value}{hd.quote(key.text)} "
                f"{key.at.astimezone(tz=tz_game).time()} "
                f"{key.player.name_mention}</li>"
            )
        text += "</ol>"
    return text


def to_emoji(key: dto.KeyTime) -> KeyEmoji:
    if key.is_duplicate:
        return KeyEmoji.duplicate
    if key.is_correct:
        return KeyEmoji.correct
    return KeyEmoji.incorrect
