from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    ScrollingGroup,
    Select,
    SwitchTo,
    Button,
    Calendar,
    Cancel,
    Start,
    WebApp,
)
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format, Case, Jinja

from shvatka.tgbot import states
from .getters import (
    get_my_games,
    get_game,
    get_game_time,
    get_game_datetime,
    get_games,
    get_completed_game,
    get_game_waivers,
    get_game_results,
    get_game_keys,
    get_game_with_channel,
)
from .handlers import (
    select_my_game,
    start_waivers,
    select_date,
    process_time_message,
    schedule_game,
    show_scn,
    start_schedule_game,
    show_zip_scn,
    show_game_orgs,
    cancel_scheduled_game,
    rename_game_handler,
    publish_game,
    select_game,
    show_my_game_orgs,
    show_my_zip_scn,
    get_excel_results_handler,
    to_publish_game_forum,
    complete_game_handler,
)
from shvatka.tgbot.dialogs.preview_data import PREVIEW_GAME, PreviewSwitchTo, PreviewStart

games = Dialog(
    Window(
        Const("Список прошедших"),
        ScrollingGroup(
            Select(
                Format("{item.name}"),
                id="games",
                item_id_getter=lambda x: x.id,
                items="games",
                on_click=select_game,
            ),
            id="games_sg",
            width=1,
            height=10,
        ),
        Cancel(Const("🔙Назад")),
        state=states.CompletedGamesPanelSG.list,
        getter=get_games,
        preview_data={"games": [PREVIEW_GAME]},
        preview_add_transitions=[PreviewSwitchTo(states.CompletedGamesPanelSG.game)],
    ),
    Window(
        Jinja(
            "Выбрана игра: <b>{{game.name}}</b> под номером {{game.number}}\n"
            "которая началась: {{ game.start_at|user_timezone }} "
        ),
        Button(
            Const("👥Организаторы"),
            id="game_orgs",
            on_click=show_game_orgs,
            when=~F["game"].author.is_dummy,
        ),
        SwitchTo(
            Const("📝Вейверы"),
            id="to_waivers",
            state=states.CompletedGamesPanelSG.waivers,
        ),
        SwitchTo(
            Const("📈Результаты"),
            id="to_results",
            state=states.CompletedGamesPanelSG.results,
        ),
        SwitchTo(
            Const("🔑Лог ключей"),
            id="to_keys",
            state=states.CompletedGamesPanelSG.keys,
        ),
        Button(
            Const("📦zip-сценарий"),
            id="game_zip_scn",
            on_click=show_zip_scn,
        ),
        SwitchTo(
            Const("Сценарий игры в tg"),
            id="game_scn_channel",
            state=states.CompletedGamesPanelSG.scenario_channel,
            when=F["game"].results.published_chanel_id,
        ),
        WebApp(
            url=Format("{webapp_url}"),
            text=Const("Сценарий игры на сайте"),
        ),
        SwitchTo(
            Const("🔙Назад к списку игр"),
            id="to_games",
            state=states.CompletedGamesPanelSG.list,
        ),
        state=states.CompletedGamesPanelSG.game,
        getter=get_completed_game,
        preview_data={"game": PREVIEW_GAME},
        preview_add_transitions=[
            PreviewStart(states.GameOrgsSG.orgs_list),
        ],
    ),
    Window(
        Jinja(
            "Выбрана игра №{{game.number}} <b>{{game.name}}</b>\n"
            "которая началась: {{ game.start_at|user_timezone }} "
            "{% for team, user_waivers in waivers.items() %}"
            "<b>{{team.name}}</b>:\n"
            "{% for voted in user_waivers %}"
            "{{voted.pit | player_emoji}}"
            "{% if voted.player.get_chat_id() %}"
            '<a href="tg://user?id={{voted.player.get_chat_id()}}">'
            "{{voted.player.name_mention}}"
            "</a>\n"
            "{% else %}"
            "{{voted.player.name_mention}}\n"
            "{% endif %}"
            "{% endfor %}"
            "\n\n"
            "{% endfor %}"
        ),
        SwitchTo(
            Const("⤴Назад"),
            id="to_game",
            state=states.CompletedGamesPanelSG.game,
        ),
        SwitchTo(
            Const("🔙Назад к списку игр"),
            id="to_games",
            state=states.CompletedGamesPanelSG.list,
        ),
        getter=get_game_waivers,
        state=states.CompletedGamesPanelSG.waivers,
    ),
    Window(
        DynamicMedia(selector="results.png"),
        Jinja(
            "Выбрана игра №{{game.number}} <b>{{game.name}}</b>\n"
            "которая началась: {{ game.start_at|user_timezone }} "
        ),
        Button(
            Const("📶Таблицей"),
            id="as_excel",
            on_click=get_excel_results_handler,
        ),
        SwitchTo(
            Const("🔙Назад к списку игр"),
            id="to_games",
            state=states.CompletedGamesPanelSG.list,
        ),
        SwitchTo(
            Const("⤴Назад"),
            id="to_game",
            state=states.CompletedGamesPanelSG.game,
        ),
        getter=get_game_results,
        state=states.CompletedGamesPanelSG.results,
    ),
    Window(
        Jinja("Сценарий игры тут: {{invite}}\n"),
        SwitchTo(
            Const("🔙Назад к списку игр"),
            id="to_games",
            state=states.CompletedGamesPanelSG.list,
        ),
        SwitchTo(
            Const("⤴Назад"),
            id="to_game",
            state=states.CompletedGamesPanelSG.game,
        ),
        getter=get_game_with_channel,
        state=states.CompletedGamesPanelSG.scenario_channel,
    ),
    Window(
        Jinja(
            "Лог ключей \n"
            "для игры #{{game.number}} <b>{{game.name}}</b> "
            "(началась в {{game.start_at|user_timezone}}) \n"
            "{% if key_link %}"
            'доступен <a href="{{key_link}}">по ссылке</a>'
            "{% else %}"
            "почему-то недоступен"
            "{% endif %}"
        ),
        SwitchTo(
            Const("🔙Назад к списку игр"),
            id="to_games",
            state=states.CompletedGamesPanelSG.list,
        ),
        SwitchTo(
            Const("🔙Назад"),
            id="to_game",
            state=states.CompletedGamesPanelSG.game,
        ),
        getter=get_game_keys,
        state=states.CompletedGamesPanelSG.keys,
    ),
)

my_games = Dialog(
    Window(
        Const("Список игр твоего авторства"),
        Start(Const("✍Написать игру"), id="write_game", state=states.GameWriteSG.game_name),
        Start(Const("✍Написать уровень"), id="write_level", state=states.LevelSG.level_id),
        Start(Const("🗂Уровни"), id="levels", state=states.LevelListSG.levels),
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
        Cancel(Const("🔙Назад")),
        state=states.MyGamesPanelSG.choose_game,
        getter=get_my_games,
        preview_data={"games": [PREVIEW_GAME]},
        preview_add_transitions=[PreviewSwitchTo(states.MyGamesPanelSG.game_menu)],
    ),
    Window(
        Jinja(
            "Выбрана игра: <b>{{game.name}}</b> с ID {{game.id}}\n"
            "Текущий статус: <b>{{game.status | game_status}}</b>\n"
            "{% if game.levels_count %}"
            "Количество уровней: <b>{{game.levels_count}}</b>\n"
            "{% else %}"
            "\n\n❗️<b><u>В игре ещё нет ни одного уровня!</u></b>❗️\n\n"
            "{% endif %}"
            "Дата и время начала: {% if game.start_at %} "
            "{{ game.start_at|user_timezone }} "
            "{% else %} "
            "не запланирована"
            "{% endif %}"
        ),
        Button(
            Const("📜Сценарий"),
            id="game_scn",
            on_click=show_scn,
            when=F["game"].can_be_edited,
        ),
        Button(
            Const("👥Организаторы"),
            id="game_orgs",
            on_click=show_my_game_orgs,
            when=F["game"].can_be_edited,
        ),
        Button(
            Const("📦zip-сценарий"),
            id="game_zip_scn",
            on_click=show_my_zip_scn,
        ),
        SwitchTo(
            Const("✏Переименовать"),
            id="game_rename",
            state=states.MyGamesPanelSG.rename,
            when=F["game"].can_change_name,
        ),
        Button(
            Const("📝Начать сборку вейверов"),
            id="start_waiver",
            on_click=start_waivers,
            when=F["game"].can_start_waivers,
        ),
        Button(
            Const("📨Опубликовать"),
            id="game_publish",
            on_click=publish_game,
            when=F["game"].can_be_publish,
        ),
        Button(
            Const("📨Опубликовать на форуме"),
            id="game_forum_publish",
            on_click=to_publish_game_forum,
            when=F["game"].can_be_publish,
        ),
        Button(
            Const("✅Завершить (в прошедшие игры)"),
            id="complete_game",
            on_click=complete_game_handler,
            when=F["game"].results.published_chanel_id,
        ),
        Button(
            Const("📆Запланировать игру"),
            id="start_schedule_game",
            on_click=start_schedule_game,
            when=F["game"].can_set_start_datetime,
        ),
        Button(
            Const("📥Отменить игру"),
            id="cancel_scheduled_game",
            on_click=cancel_scheduled_game,
            when=F["game"].start_at & F["game"].can_set_start_datetime,
        ),
        SwitchTo(
            Const("🔙Назад к списку игр"),
            id="to_my_games",
            state=states.MyGamesPanelSG.choose_game,
        ),
        state=states.MyGamesPanelSG.game_menu,
        getter=get_game,
        preview_data={"game": PREVIEW_GAME},
        preview_add_transitions=[
            PreviewStart(states.GameEditSG.current_levels),
            PreviewStart(states.GameOrgsSG.orgs_list),
            PreviewStart(states.GamePublishSG.prepare),
            PreviewStart(states.GamePublishSG.forum),
            Cancel(),
            PreviewStart(states.GameScheduleSG.date),
        ],
    ),
    Window(
        Jinja("Чтобы переименовать игру {{game.name}} пришли новое имя"),
        MessageInput(func=rename_game_handler),
        SwitchTo(Const("🔙Назад"), id="back", state=states.MyGamesPanelSG.game_menu),
        state=states.MyGamesPanelSG.rename,
        getter=get_game,
    ),
)


schedule_game_dialog = Dialog(
    Window(
        Jinja("Выбор даты начала игры <b>{{game.name}}</b>"),
        Calendar(id="select_game_play_date", on_click=select_date),
        Cancel(Const("🔙Назад")),
        state=states.GameScheduleSG.date,
        getter=get_game,
        preview_data={"game": PREVIEW_GAME},
        preview_add_transitions=[PreviewSwitchTo(states.GameScheduleSG.time)],
    ),
    Window(
        Case(
            {
                False: Const("Введите время в формате ЧЧ:ММ"),
                True: Jinja(
                    "Будет сохранено: {{scheduled_time}}. "
                    'Нажмите "Далее", если уверены, '
                    "или отправьте другое время в формате ЧЧ:ММ вместо этого"
                ),
            },
            selector="has_time",
        ),
        MessageInput(func=process_time_message),
        SwitchTo(
            Const("📆Сохранить"),
            id="save_game_schedule",
            state=states.GameScheduleSG.confirm,
            when=lambda data, *args: data["has_time"],
        ),
        Cancel(Const("🔙Назад")),
        getter=get_game_time,
        preview_data={"game": PREVIEW_GAME, "has_time": True},
        state=states.GameScheduleSG.time,
    ),
    Window(
        Jinja(
            "Для игры <b>{{game.name}}</b> c id {{game.id}} "
            "будет установлено время начала игры "
            "{{scheduled_datetime|user_timezone}} "
            "Если сохранить игра самопроизвольно начнётся в это время.\n\n"
            "Сохранить?"
        ),
        Button(
            Const("✅Да"),
            id="save_scheduled_dt",
            on_click=schedule_game,
        ),
        Cancel(Const("❌Отменить")),
        getter=get_game_datetime,
        preview_data={"game": PREVIEW_GAME},
        state=states.GameScheduleSG.confirm,
    ),
)
