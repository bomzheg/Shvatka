from dataclasses import dataclass

from aiogram.types import BotCommand


@dataclass
class CommandsGroup:
    group_name: str
    commands: list[BotCommand]

    def __str__(self):
        return f"{self.group_name}\n" + "\n".join(
            map(lambda x: f"/{x.command} - {x.description}", self.commands))


START_COMMAND = BotCommand(command="start", description="начало работы с ботом")
HELP_COMMAND = BotCommand(command="help", description="помощь")
ABOUT_COMMAND = BotCommand(command="about", description="о боте")
CANCEL_COMMAND = BotCommand(command="cancel", description="отмена начатого диалога")
CHAT_ID_COMMAND = BotCommand(command="chat_id", description="узнать chat_id данного чата")
CHAT_TYPE_COMMAND = BotCommand(command="chat_type", description="узнать chat_id данного чата")

CREATE_TEAM_COMMAND = BotCommand(
    command="create_team", description="создать команду на базе текущего чата"
)
ADD_IN_TEAM_COMMAND = BotCommand(
    command="add_in_team", description="добавить в команду игрока (реплаем по игроку)"
)
MANAGE_TEAM_COMMAND = BotCommand(
    command="manage_team", description="открыть меню управления командой"
)
REMOVE_FROM_TEAM_COMMAND = BotCommand(
    command="remove_from_team", description="удалить игрока из команды (реплаем по игроку)"
)
START_WAIVERS_COMMAND = BotCommand(command="waivers", description="начать сборку вейверов")
APPROVE_WAIVERS_COMMAND = BotCommand(
    command="approve_waivers", description="закрыть сборку вейверов"
)

STATUS_COMMAND = BotCommand(command="status", description="статус схватки")
TEAM_COMMAND = BotCommand(command="team", description="команда")
TEAMS_COMMAND = BotCommand(command="teams", description="список команд")
PLAYERS_COMMAND = BotCommand(command="players", description="игроки команды")
ALL_PLAYERS_COMMAND = BotCommand(command="all_players", description="игроки команды")
ME_COMMAND = BotCommand(command="me", description="мой профиль")
LEAVE_COMMAND = BotCommand(command="leave", description="выйти из команды")
GAMES_COMMAND = BotCommand(command="games", description="список игр")

GET_WAIVERS_COMMAND = BotCommand(command="get_waivers", description="показать текущие вейверы")
SPY_COMMAND = BotCommand(
    command="spy", description="показать на каких уровнях команды (только во время игры)"
)
GET_KEYS_COMMAND = BotCommand(
    command="log_keys", description="получить введённые ключи (только во время игры)"
)

HELP_BASE = CommandsGroup("Базовые команды:", [
    START_COMMAND, HELP_COMMAND, ABOUT_COMMAND, CANCEL_COMMAND, CHAT_ID_COMMAND,
    CHAT_TYPE_COMMAND,
])
UPDATE_COMMANDS = BotCommand(command="update_commands", description="обновить команды бота")
EXCEPTION_COMMAND = BotCommand(command="exception", description="сгенерировать исключение")
GET_OUT = BotCommand(command="get_out", description="бот, уходи из чата!")
HELP_ADMIN = CommandsGroup("Команды администратора бота:", [
    BotCommand(command="jobs", description="запланированные функции"),
    BotCommand(command="cancel_jobs", description="отменить запланированные функции"),
    EXCEPTION_COMMAND,
    UPDATE_COMMANDS,
    GET_OUT,
])
MY_GAMES_COMMAND = BotCommand(command="my_games", description="мои игры (включая черновики)")
NEW_LEVEL_COMMAND = BotCommand(command="new_level", description="новый уровень")
HELP_ORG = CommandsGroup("Команды для организаторов:", [
    MY_GAMES_COMMAND,
    BotCommand(
        command="new_game", description="начать сборку новой игры из ранее написанных уровней"
    ),
    BotCommand(command="levels", description="показать список игр"),
    NEW_LEVEL_COMMAND,
    GET_WAIVERS_COMMAND,
    SPY_COMMAND,
    GET_KEYS_COMMAND,
])

HELP_TEAM = CommandsGroup("Команды для управления командой:", [
    CREATE_TEAM_COMMAND,
    ADD_IN_TEAM_COMMAND,
    MANAGE_TEAM_COMMAND,
    REMOVE_FROM_TEAM_COMMAND,
    START_WAIVERS_COMMAND,
    APPROVE_WAIVERS_COMMAND,
])
HELP_INFO = CommandsGroup("Другие команды:", [
    STATUS_COMMAND, TEAM_COMMAND, PLAYERS_COMMAND, ME_COMMAND, GAMES_COMMAND, LEAVE_COMMAND,
])
HELP_USER = "\n\n".join(map(str, (HELP_BASE, HELP_ORG, HELP_TEAM, HELP_INFO,)))
HELP_USER_ADMIN = "\n\n".join(map(str, (HELP_BASE, HELP_ORG, HELP_TEAM, HELP_INFO, HELP_ADMIN,)))

DEFAULT_COMMANDS = [
    HELP_COMMAND, GAMES_COMMAND, STATUS_COMMAND, CANCEL_COMMAND, TEAM_COMMAND, ME_COMMAND,
]
