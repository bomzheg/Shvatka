from aiogram.enums import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Cancel, ScrollingGroup, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Jinja

from shvatka.tgbot import states
from shvatka.tgbot.dialogs.preview_data import (
    PREVIEW_FORUM_TEAM,
    PREVIEW_FORUM_TEAMS,
    PREVIEW_FORUM_USER,
    PREVIEW_TEAM,
    PreviewSwitchTo,
)

from .getters import get_forum_team, get_forum_teams, get_forum_user, get_team
from .handlers import confirm_merge, confirm_merge_player, player_link_handler, select_forum_team

merge_teams_dialog = Dialog(
    Window(
        Jinja(
            "🔮 Былые свершения.\n"
            "\n"
            "Чтобы вспомнить былые свершения нужно найти команду, как она выглядела на форуме.\n"
            "Хочешь объединить команду {{team.name}} со своей форумной копией?"
        ),
        SwitchTo(
            Const("Да, время выбирать"),
            id="to_forum_list",
            state=states.MergeTeamsSG.list_forum,
        ),
        Cancel(Const("🔙Ой нет, это я случайно")),
        getter=get_team,
        state=states.MergeTeamsSG.main,
        preview_data={"team": PREVIEW_TEAM},
    ),
    Window(
        Jinja("Итак мы ищем форумную версию для команды {{team.name}}"),
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
        Cancel(Const("🔙Не надо ничего объединять")),
        getter=(get_team, get_forum_teams),
        state=states.MergeTeamsSG.list_forum,
        preview_data={"team": PREVIEW_TEAM, "forum_teams": PREVIEW_FORUM_TEAMS},
        preview_add_transitions=[PreviewSwitchTo(states.MergeTeamsSG.confirm)],
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
        preview_data={"team": PREVIEW_TEAM, "forum_team": PREVIEW_FORUM_TEAM},
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
        SwitchTo(
            Const("Да, время выбирать"),
            id="to_forum_list",
            state=states.MergePlayersSG.input,
        ),
        Cancel(Const("🔙Ой нет, это я случайно")),
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
        preview_add_transitions=[PreviewSwitchTo(states.MergePlayersSG.confirm)],
    ),
    Window(
        Jinja("Объединить свои достижения с {{forum_user.name}}?"),
        SwitchTo(
            Const("Нет, это не я. Назад"),
            id="to_forum_list",
            state=states.MergePlayersSG.input,
        ),
        Button(
            Const("Ага, это я"),
            id="confirm",
            on_click=confirm_merge_player,
        ),
        Cancel(Const("🔙Я передумал, не надо")),
        getter=get_forum_user,
        state=states.MergePlayersSG.confirm,
        preview_data={"forum_user": PREVIEW_FORUM_USER},
    ),
)
