from aiogram.enums import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Cancel, SwitchTo, ScrollingGroup, Select, Button
from aiogram_dialog.widgets.text import Jinja, Const

from shvatka.tgbot import states
from .getters import get_team, get_forum_team, get_forum_teams, get_forum_user
from .handlers import select_forum_team, confirm_merge, player_link_handler

merge_teams_dialog = Dialog(
    Window(
        Jinja(
            "🔮 Былые свершения.\n"
            "\n"
            "Чтобы вспомнить былые свершения нужно найти команду, как она выглядела на форуме.\n"
            "Хочешь объединить команду {{team.name}} со своей форумной копией?"
        ),
        Cancel(Const("🔙Ой нет, это я случайно")),
        SwitchTo(
            Const("Да, время выбирать"),
            id="to_forum_list",
            state=states.MergeTeamsSG.list_forum,
        ),
        getter=get_team,
        state=states.MergeTeamsSG.main,
    ),
    Window(
        Jinja("Итак мы ищем форумную версию для команды {{team.name}}"),
        Cancel(Const("🔙Не надо ничего объединять")),
        ScrollingGroup(
            Select(
                Jinja("🚩{{item.name}}"),
                id="forum_teams",
                item_id_getter=lambda x: x.id,
                items="forum_teams",
                on_click=select_forum_team,
            ),
            id="forum_teams_sg",
            width=1,
            height=10,
        ),
        getter=(get_team, get_forum_teams),
        state=states.MergeTeamsSG.list_forum,
    ),
    Window(
        Jinja(
            "Объединяем команду <b>{{team.name}}</b> в боте "
            "с командой на форуме <b>{{forum_team.name}}</b>?"
        ),
        Cancel(Const("🔙Не надо ничего объединять")),
        Button(
            Const("Да, объединить"),
            id="confirm_merge",
            on_click=confirm_merge,
        ),
        Cancel(Const("🔙Нет!!")),
        getter=(get_team, get_forum_team),
        state=states.MergeTeamsSG.confirm,
    ),
)


merge_player_dialog = Dialog(
    Window(
        Jinja(
            "🔮 Былые свершения.\n"
            "\n"
            "Чтобы вспомнить былые свершения нужно найти своего персонажа, "
            "как он выглядел на форуме.\n"
            "Хочешь объединить свои достижения тут со своей форумной копией?"
        ),
        Cancel(Const("🔙Ой нет, это я случайно")),
        SwitchTo(
            Const("Да, время выбирать"),
            id="to_forum_list",
            state=states.MergePlayersSG.input,
        ),
        state=states.MergePlayersSG.main,
    ),
    Window(
        Const(
            "Отлично. Чтобы соединить свои достижения тут и на форуме, "
            "нужно прислать мне ссылку на своего персонажа на форуме, например \n"
            "<code>http://www.shvatka.ru/index.php?showuser=6767</code>"
        ),
        Cancel(Const("🔙Я передумал, не надо")),
        MessageInput(func=player_link_handler, content_types=ContentType.TEXT),
        state=states.MergePlayersSG.input,
    ),
    Window(
        Jinja("Объединить свои достижения с {{forum_user.name}}?"),
        Cancel(Const("🔙Я передумал, не надо")),
        SwitchTo(
            Const("Нет, это не я. Назад"),
            id="to_forum_list",
            state=states.MergePlayersSG.input,
        ),
        getter=get_forum_user,
        state=states.MergePlayersSG.confirm,
    ),
)
