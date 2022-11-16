from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Cancel, Start
from aiogram_dialog.widgets.text import Const, Format, Jinja

from tgbot.states import MyGamesPanel, MainMenu, Promotion, OrgSpy
from .getters import get_promotion_token, get_main
from ..widgets.switch_inline import SwitchInlineQuery

main_menu = Dialog(
    Window(
        Jinja(
            "Привет, {{player.user.name_mention}}!\n"
            "Ты находишься в главном меню.\n"
            "твой id {{player.id}}"
        ),
        Jinja(
            "Сейчас активна игра {{game.name}}.\n"
            "Статус: {{game.status}}\n",
            when=F["game"],
        ),
        Jinja(
            "Игра запланирована на {{ game.start_at|user_timezone }}",
            when=F["game"].start_at,
        ),
        Cancel(Const("❌Закрыть")),
        Start(
            Const("🗄Мои игры"),
            id="my_games",
            state=MyGamesPanel.choose_game,
            when=F["player"].can_be_author,
        ),
        Start(
            Const("👀Шпион"),
            id="game_spy",
            state=OrgSpy.main,
            when=F["org"],
        ),
        Start(
            Const("✍Поделиться полномочиями автора"),
            id="promotion",
            state=Promotion.disclaimer,
            when=F["player"].can_be_author,
        ),
        # прошедшие игры
        # ачивки
        # уровни (не привязанные к играм?)
        # promote
        state=MainMenu.main,
        getter=get_main,
    ),
)

promote_dialog = Dialog(
    Window(
        Const(
            "Чтобы наделить пользователя полномочиями нужно:\n"
            "1. нажать кнопку ниже\n"
            "2. выбрать чат с пользователем\n"
            "3. в чате с пользователем, дождавшись, над окном ввода сообщения, "
            "выбрать кнопку \"Наделить полномочиями\""
        ),
        SwitchInlineQuery(
            Const("✍Поделиться полномочиями автора"),
            Format("{inline_query}"),
        ),
        Cancel(Const("⤴Назад")),
        state=Promotion.disclaimer,
        getter=get_promotion_token,
    )
)
