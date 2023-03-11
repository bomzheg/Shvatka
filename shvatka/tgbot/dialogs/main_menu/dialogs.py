from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Cancel, Start, SwitchInlineQuery
from aiogram_dialog.widgets.text import Const, Format, Jinja

from shvatka.tgbot import states
from .getters import get_promotion_token, get_main
from ..team_manage.getters import get_my_team_

main_menu = Dialog(
    Window(
        Jinja(
            "Привет, {{player.name_mention}}!\n"
            "Ты находишься в главном меню.\n"
            "{% if team %}"
            "Ты состоишь в команде 🚩{{team.name}} "
            "в должности {{team_player|player_emoji}}{{team_player.role}}\n"
            "{% else %}"
            "Ты не состоишь в команде\n"
            "{% endif %}"
            "{% if game %}"
            "Сейчас активна игра {{game.name}}.\n"
            "Статус: {{game.status}}\n"
            "{% endif %}"
            "{% if game.start_at %}"
            "Игра запланирована на {{ game.start_at|user_timezone }}"
            "{% endif %}"
        ),
        Cancel(Const("❌Закрыть")),
        Start(
            Const("🗄Прошедшие игры"),
            id="completed_games",
            state=states.CompletedGamesPanelSG.list,
        ),
        Start(
            Const("🗂Мои игры"),
            id="my_games",
            state=states.MyGamesPanelSG.choose_game,
            when=F["player"].can_be_author,
        ),
        Start(
            Const("👀Шпион"),
            id="game_spy",
            state=states.OrgSpySG.main,
            when=F["org"],
        ),
        Start(
            Const("✍Поделиться полномочиями автора"),
            id="promotion",
            state=states.PromotionSG.disclaimer,
            when=F["player"].can_be_author,
        ),
        Start(
            Const("🚩Управление командой"),
            id="to_team_manage",
            state=states.CaptainsBridgeSG.main,
            when=(
                F["team_player"].can_manage_players
                | F["team_player"].can_change_team_name
                | F["team_player"].can_remove_players
            ),
        ),
        Start(
            Const("👥Команды"),
            id="to_teams",
            state=states.TeamsSg.list,
        ),
        # ачивки
        # уровни (не привязанные к играм?)
        state=states.MainMenuSG.main,
        getter=(get_main, get_my_team_),
    ),
)

promote_dialog = Dialog(
    Window(
        Const(
            "Чтобы наделить пользователя полномочиями нужно:\n"
            "1. нажать кнопку ниже\n"
            "2. выбрать чат с пользователем\n"
            "3. в чате с пользователем, дождавшись, над окном ввода сообщения, "
            'выбрать кнопку "Наделить полномочиями"'
        ),
        SwitchInlineQuery(
            Const("✍Поделиться полномочиями автора"),
            Format("{inline_query}"),
        ),
        Cancel(Const("⤴Назад")),
        state=states.PromotionSG.disclaimer,
        getter=get_promotion_token,
    )
)
