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
HELP_COMMAND = BotCommand(command="help", description="помощь")  # TODO
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
)  # TODO
REMOVE_FROM_TEAM_COMMAND = BotCommand(
    command="remove_from_team", description="удалить игрока из команды (реплаем по игроку)"
)  # TODO
START_WAIVERS_COMMAND = BotCommand(command="waivers", description="начать сборку вейверов")
APPROVE_WAIVERS_COMMAND = BotCommand(
    command="approve_waivers", description="закрыть сборку вейверов"
)

STATUS_COMMAND = BotCommand(command="status", description="статус схватки")  # TODO
TEAM_COMMAND = BotCommand(command="team", description="команда")
TEAMS_COMMAND = BotCommand(command="teams", description="список команд")  # TODO
PLAYERS_COMMAND = BotCommand(command="players", description="игроки команды")
ALL_PLAYERS_COMMAND = BotCommand(command="all_players", description="игроки команды")  # TODO
ME_COMMAND = BotCommand(command="me", description="мой профиль")  # TODO
LEAVE_COMMAND = BotCommand(command="leave", description="выйти из команды")
GAMES_COMMAND = BotCommand(command="games", description="список игр")  # TODO

GET_WAIVERS_COMMAND = BotCommand(command="get_waivers", description="показать текущие вейверы")
SPY_COMMAND = BotCommand(
    command="spy", description="Меню шпиона - организатора"
)
SPY_LEVELS_COMMAND = BotCommand(
    command="spy_levels", description="показать на каких уровнях команды (только во время игры)"
)
SPY_KEYS_COMMAND = BotCommand(
    command="spy_keys", description="получить введённые ключи (только во время игры)"
)

HELP_BASE = CommandsGroup("Базовые команды:", [
    START_COMMAND, HELP_COMMAND, ABOUT_COMMAND, CANCEL_COMMAND, CHAT_ID_COMMAND,
    CHAT_TYPE_COMMAND,
])
UPDATE_COMMANDS = BotCommand(command="update_commands", description="обновить команды бота")  # TODO
EXCEPTION_COMMAND = BotCommand(command="exception", description="сгенерировать исключение")
GET_OUT = BotCommand(command="get_out", description="бот, уходи из чата!")
JOBS_COMMAND = BotCommand(command="jobs", description="запланированные функции")
CANCEL_JOBS_COMMAND = BotCommand(command="cancel_jobs", description="отменить запланированные функции")
HELP_ADMIN = CommandsGroup("Команды администратора бота:", [
    JOBS_COMMAND,
    CANCEL_JOBS_COMMAND,
    EXCEPTION_COMMAND,
    UPDATE_COMMANDS,
    GET_OUT,
])
MY_GAMES_COMMAND = BotCommand(command="my_games", description="мои игры (включая черновики)")
NEW_LEVEL_COMMAND = BotCommand(command="new_level", description="новый уровень")
NEW_GAME_COMMAND = BotCommand(command="new_game", description="начать сборку новой игры из ранее написанных уровней")
LEVELS_COMMAND = BotCommand(command="levels", description="показать список уровней")  # TODO
HELP_ORG = CommandsGroup("Команды для организаторов:", [
    MY_GAMES_COMMAND,
    NEW_GAME_COMMAND,
    LEVELS_COMMAND,
    NEW_LEVEL_COMMAND,
    GET_WAIVERS_COMMAND,
    SPY_COMMAND,
    SPY_LEVELS_COMMAND,
    SPY_KEYS_COMMAND,
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
