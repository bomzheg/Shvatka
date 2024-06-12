from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Cancel, Start, SwitchInlineQuery
from aiogram_dialog.widgets.text import Const, Format, Jinja

from shvatka.core.models import enums
from shvatka.tgbot import states
from .getters import get_promotion_token, get_main

main_menu = Dialog(
    Window(
        Jinja(
            "Привет, {{player.name_mention}}!\n"
            "Ты находишься в главном меню.\n"
            "{% if team %}"
            "\n\n🚩{{team.name}}\n"
            "{{team_player|player_emoji}}{{team_player.role}}\n"
            "{% else %}"
            "Ты не состоишь в команде\n"
            "{% endif %}"
            "{% if game %}"
            "\n\nАктивная игра: <b>{{game.name}}</b> ({{game.status | game_status}})\n"
            "{% endif %}"
            "{% if game.start_at %}"
            "Игра запланирована на {{ game.start_at|user_timezone }}"
            "{% endif %}"
            "\n\n"
            "{% if org %}"
            "{% if not org.deleted %}"
            "Ты организатор. Вот твои полномочия на игру:\n"
            "{{org.can_spy | bool_emoji}} шпионить\n"
            "{{org.can_see_log_keys | bool_emoji}} смотреть лог ключей\n"
            "{% else %}"
            "Тебя удалили из организаторов. К сожалению, "
            "ты не сможешь ни играть ни участвовать в организации."
            "{% endif %}"
            "{% elif not team %}"
            "Чтобы поиграть в игру - найди себе команду, сейчас ты не состоишь ни в одной"
            "{% elif waiver %}"
            "{% if waiver.played.can_play %}"
            "Ты <b>будешь играть</b> в эту игру"
            "{% elif waiver.played.is_deny %}"
            "Получен твой <b>отказ</b> играть в эту игру"
            "{% elif waiver.played.cant_decide %}"
            "От тебя <b>не поступило</b> итогового решения по игре"
            "{% elif waiver.played.is_revoked %}"
            "Твой капитан <b>исключил тебя</b> из списков на игру"
            "{% elif waiver.played.is_not_allowed %}"
            "Орги <b>не приняли</b> твою заявку на игру"
            "{% endif %}"
            "{% endif %}"
        ),
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
            when=F["org"] & F["game"].status == enums.GameStatus.finished,
        ),
        Start(
            Const("✍Аппрувнуть друга"),
            id="promotion",
            state=states.PromotionSG.disclaimer,
            when=F["player"].can_be_author,
        ),
        Start(
            Const("🚩Моя команда"),
            id="my_team",
            state=states.MyTeamSg.team,
            when=F["team"],
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
        Start(
            Const("🔮Былые свершения"),
            id="to_merge_player",
            state=states.MergePlayersSG.main,
            when=~F["player"].has_forum_user(),
        ),
        Cancel(Const("❌Закрыть")),
        # ачивки
        state=states.MainMenuSG.main,
        getter=get_main,
    ),
)

promote_dialog = Dialog(
    Window(
        Const(
            "Аппрув нужен игрокам, которые хотят создавать свою команду "
            "или писать свои игры.\n"
            "\n"
            "Пожалуйста, прежде чем кого-то аппрувить - убедитесь, "
            "что знаете этого схватчика лично! Люди с аппрувом могут портить всем игру."
            "\n\n"
            "Чтобы наделить пользователя полномочиями нужно:\n"
            "1. нажать кнопку ниже\n"
            "2. выбрать чат личных сообщений с пользователем\n"
            "3. в чате с пользователем, дождавшись, над окном ввода сообщения, "
            'выбрать кнопку "Наделить полномочиями"'
        ),
        SwitchInlineQuery(
            Const("✍Аппрувнуть"),
            Format("{inline_query}"),
        ),
        Cancel(Const("🔙Назад")),
        state=states.PromotionSG.disclaimer,
        getter=get_promotion_token,
    )
)
