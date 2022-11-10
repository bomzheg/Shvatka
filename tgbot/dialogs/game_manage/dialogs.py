from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import ScrollingGroup, Select, SwitchTo, Button, Calendar
from aiogram_dialog.widgets.text import Const, Format, Case, Jinja

from tgbot.states import MyGamesPanel, GameSchedule
from .getters import get_my_games, get_game, not_getting_waivers, is_getting_waivers, get_game_time, \
    get_game_datetime
from .handlers import select_my_game, start_waivers, select_date, process_time_message, schedule_game, show_scn, \
    start_schedule_game, show_zip_scn, show_game_orgs
from ..preview_data import PREVIEW_GAME

games = Dialog(
    Window(
        Const("Список игр твоего авторства"),
        ScrollingGroup(
            Select(
                Format("{item.name}"),
                id="my_games",
                item_id_getter=lambda x: x.id,
                items="games",
                on_click=select_my_game,
            ),
            id="my_games_sg",
            width=1,
            height=10,
        ),
        state=MyGamesPanel.choose_game,
        preview_data={"games": [PREVIEW_GAME]},
        getter=get_my_games,
    ),
    Window(
        Format(
            "Редактирование <b>{game.name}</b>\n"
            "текущий статус: <b>{game.status}</b>\n"
        ),
        SwitchTo(
            Const("Назад к списку игр"),
            id="to_my_games",
            state=MyGamesPanel.choose_game,
        ),
        Button(
            Const("Сценарий"),
            id="game_scn",
            on_click=show_scn,
        ),
        Button(
            Const("Организаторы"),
            id="game_orgs",
            on_click=show_game_orgs,
        ),
        Button(
            Const("zip-сценарий"),
            id="game_zip_scn",
            on_click=show_zip_scn,
        ),
        Button(
            Const("Начать сборку вейверов"),
            id="start_waiver",
            on_click=start_waivers,
            when=not_getting_waivers,
        ),
        Button(
            Const("Запланировать игру"),
            id="start_schedule_game",
            on_click=start_schedule_game,
            when=is_getting_waivers,
        ),
        state=MyGamesPanel.game_menu,
        preview_data={"game": PREVIEW_GAME},
        getter=get_game,
    ),
)


schedule_game_dialog = Dialog(
    Window(
        Format("Выбор даты начала игры <b>{game.name}</b>"),
        Calendar(id='select_game_play_date', on_click=select_date),
        state=GameSchedule.date,
        preview_data={"game": PREVIEW_GAME},
        getter=get_game,
    ),
    Window(
        Case(
            {
                False: Const("Введите время в формате ЧЧ:ММ"),
                True: Format(
                    "Будет сохранено: {scheduled_time}. "
                    "Нажмите \"Далее\", если уверены, "
                    "или отправьте другое время в формате ЧЧ:ММ вместо этого"
                ),
            },
            selector="has_time",
        ),
        MessageInput(func=process_time_message),
        SwitchTo(
            Const("Сохранить"),
            id="save_game_schedule",
            state=GameSchedule.confirm,
            when=lambda data, *args: data["has_time"],
        ),
        getter=get_game_time,
        preview_data={"game": PREVIEW_GAME, "has_time": True},
        state=GameSchedule.time,
    ),
    Window(
        Jinja(
            "Для игры <b>{{game.name}}</b> c id {{game.id}} "
            "будет установлено время начала игры {{scheduled_datetime}} "
            "Если сохранить игра самопроизвольно начнётся в это время.\n\n"
            "Сохранить?"
        ),
        Button(
            Const("Да"),
            id="save_scheduled_dt",
            on_click=schedule_game,
        ),
        getter=get_game_datetime,
        preview_data={"game": PREVIEW_GAME},
        state=GameSchedule.confirm,
    ),
)
