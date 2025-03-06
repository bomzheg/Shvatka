import enum
from datetime import datetime
from typing import Any

from aiogram.utils.text_decorations import html_decoration as hd
from telegraph.aio import Telegraph

from shvatka.core.models import dto, enums
from shvatka.core.models.dto import scn, action
from shvatka.core.services.game_stat import get_typed_keys
from shvatka.core.utils.datetime_utils import tz_game, DATETIME_FORMAT
from shvatka.infrastructure.db.dao.holder import HolderDao


class KeyEmoji(enum.Enum):
    correct = "✅"
    incorrect = "❌"
    duplicate = "💤"
    bonus = "💰"
    unknown = "❔"

    @classmethod
    def from_key(cls, key: dto.KeyTime) -> "KeyEmoji":
        if key.is_duplicate:
            return KeyEmoji.duplicate
        match key.type_:
            case enums.KeyType.simple:
                return KeyEmoji.correct
            case enums.KeyType.wrong:
                return KeyEmoji.incorrect
            case enums.KeyType.bonus:
                return KeyEmoji.bonus
        return KeyEmoji.unknown


def render_log_keys(log_keys: dict[dto.Team, list[dto.KeyTime]]) -> str:
    text = f"<h3>Лог ключей на {datetime.now(tz=tz_game).strftime(DATETIME_FORMAT)}:</h3><br/>"
    for team, keys in log_keys.items():
        text += f"<h4>🚩{hd.quote(team.name)}:</h4>"
        n_level = keys[0].level_number - 1
        for i, key in enumerate(keys):
            if n_level != key.level_number:
                # keys are sorted, so is previous and next level not equals - add caption
                n_level = key.level_number
                if i > 0:
                    text += "</ol><br/>"
                text += f"Уровень №{n_level + 1}<br/><ol>"
            text += (
                f"<li>{KeyEmoji.from_key(key).value}{hd.quote(key.text)} "
                f"{key.at.astimezone(tz=tz_game).time().isoformat()} "
                f"{key.player.name_mention}</li>"
            )
        text += "</ol><hr/><hr/><hr/>"
    return text


async def create_keys_page(
    game: dto.Game, player: dto.Player, telegraph: Telegraph, dao: HolderDao, salt: str = ""
) -> dict[str, Any]:
    keys = await get_typed_keys(game=game, player=player, dao=dao.typed_keys)
    text = render_log_keys(keys)
    page = await telegraph.create_page(
        title=f"{salt} Лог ключей игры {game.name}",
        html_content="boilerplate",
    )
    await telegraph.edit_page(
        path=page["path"],
        title=f"Лог ключей игры {game.name}",
        html_content=text,
    )
    return page


async def get_or_create_keys_page(
    game: dto.Game, player: dto.Player, telegraph: Telegraph, dao: HolderDao
) -> str:
    if game.results.keys_url:
        return game.results.keys_url
    page = await create_keys_page(game, player, telegraph, dao)
    await dao.game.set_keys_url(game, page["url"])
    await dao.game.commit()
    game.results.keys_url = page["url"]
    assert game.results.keys_url is not None
    return game.results.keys_url


def render_level_keys(level: scn.LevelScenario) -> str:
    text = ""
    for c in level.conditions:
        if not isinstance(c, action.KeyWinCondition):
            continue
        text += f"🗝🗝🗝{' -> ' + c.next_level if c.next_level else ''}\n"
        for k in c.keys:
            text += f"🔑 {k}\n"
    if level.get_bonus_keys():
        text += "\nБонусные ключи:\n💰 " + "\n💰 ".join(
            [f"{b.text} ({b.bonus_minutes} мин.)" for b in level.get_bonus_keys()]
        )
    return text
