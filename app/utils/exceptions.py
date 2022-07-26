"""
Иерархия исключений:
SHError
|-ScenarioNotCorrect (ValueError)
|-FileNotFound (AttributeError)
|-ActionCantBeNow
|-SHDataBreach
|-GameError
| |-GameStatusError
| | |-AnotherGameIsActive
| | | |-AnotherGameWasStarted
| | |
| | |-GameNotCompleted
| | |-CantDeleteActiveGame
| | |-CantDeleteCompletedGame
| | |-GameNotFinished
| |-GameNotFound
|-PermissionsError
| |-CantBeAuthor
"""


class SHError(Exception):
    notify_user = "Ошибка"

    def __init__(
        self,
        text: str = "",
        user_id: int = None,
        chat_id: int = None,
        team_id: int = None,
        game_id: int = None,
        alarm: bool = False,
        *args,
        **kwargs
    ):
        super(SHError, self).__init__(args, kwargs)
        self.text = text
        self.user_id = user_id
        self.chat_id = chat_id
        self.team_id = team_id
        self.game_id = game_id
        self.alarm = alarm

    def __str__(self):
        result_msg = f"Error: {self.text}"
        if self.user_id:
            result_msg += f", by user {self.user_id}"
        if self.chat_id:
            result_msg += f", in chat {self.chat_id}"
        if self.team_id:
            result_msg += f", team {self.team_id}"
        if self.notify_user:
            result_msg += f". Information for user: {self.notify_user}"
        return result_msg


class ScenarioNotCorrect(SHError):
    notify_user = "JSON-файл некорректен"

    def __init__(self, *args, level_id: int = None, **kwargs):
        super(ScenarioNotCorrect, self).__init__(*args, **kwargs)
        self.level_id = level_id

    def __str__(self):
        result = super().__str__()
        if self.level_id:
            result += f"\nProblem level_id: {self.level_id}"
        return result


class FileNotFound(SHError, AttributeError):
    notify_user = "Файл не найден"


class ActionCantBeNow(SHError):
    notify_user = "Действие не может быть выполнено сейчас"


class SHDataBreach(SHError):
    notify_user = "Действие приведёт к нарушению целостности данных"


class SaltNotExist(SHError):
    def __init__(
        self,
        salt: str = None,
        *args,
        **kwargs
    ):
        super(SaltNotExist, self).__init__(*args, **kwargs)
        self.salt = salt

    notify_user = "Этот запрос устарел, попробуйте ещё раз"


class GameError(SHError):
    notify_user = "Ошибка связанная с игрой"


class GameStatusError(GameError):
    def __init__(
        self,
        game_status: str = None,
        *args,
        **kwargs
    ):
        super(GameStatusError, self).__init__(*args, **kwargs)
        self.game_status = game_status

    notify_user = "Статус игры не соответствует запрошенному действию"


class AnotherGameIsActive(GameStatusError):
    notify_user = (
        "Другая игра уже помечена активной, т.е. "
        "собирает вейверы, начата, или награждение не проведено"
    )


class HaveNotActiveGame(GameStatusError):
    notify_user = (
        "Нет игры, которая была бы помечена активной, т.е. "
        "собирала вейверы, начата, или не закончена"
    )


class AnotherGameWasStarted(AnotherGameIsActive):
    notify_user = "Другая игра уже начата"


class GameNotCompleted(GameStatusError):
    notify_user = "Данная игра не завершена. Невозможно отобразить её данные"


class CantDeleteActiveGame(GameStatusError):
    notify_user = "Нельзя удалить игру которая сейчас активна"


class CantEditGame(GameStatusError):
    notify_user = "Нельзя удалить игру которая сейчас активна или завершена"


class CantDeleteCompletedGame(GameStatusError):
    notify_user = "Нельзя удалить завершённую игру"


class GameNotFinished(GameStatusError):
    notify_user = "Игра не завершена. Данное действие можно выполнить только с завершённой игрой"


class GameNotFound(GameError, AttributeError):
    notify_user = "Игра не найдена"


class LevelError(SHError):
    notify_user = "Ошибка связанная с уровнем"

    def __init__(self, level_id: int, *args, **kwargs):
        super(LevelError, self).__init__(*args, **kwargs)
        self.level_id = level_id


class LevelNotLinked(LevelError):
    notify_user = "Уровень не привязан к игре"


class PermissionsError(SHError):
    notify_user = "Ошибка связанная с полномочиями"

    def __init__(
        self,
        permission_name: str = None,
        *args,
        **kwargs
    ):
        super(PermissionsError, self).__init__(*args, **kwargs)
        self.permission_name = permission_name


class CantBeAuthor(PermissionsError):
    notify_user = "Пользователь не имеет права быть автором"
    permission_name = "can_be_author"


class TestingNotAllowed(PermissionsError, LevelError):
    notify_user = "Тестирование этого уровня не доступно для этого пользователя"
    permission_name = "level_test"


class UserTeamError(SHError):
    notify_user = "Проблема связанные с членством игрока в команде"


class UserNotInTeam(UserTeamError):
    notify_user = "Игрок не в команде"


class UserWithoutUserIdError(SHError):
    def __init__(self, username: str = None, **kwargs):
        super().__init__(**kwargs)
        self.username = username
        self.text = "Не удалось найти пользователя по username"
