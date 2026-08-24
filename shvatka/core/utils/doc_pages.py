from enum import StrEnum


class DocPage(StrEnum):
    """A page of the user documentation an error can point the user at.

    The value is the page path inside the ROOT module of the docs
    (``docs/modules/ROOT/pages/<value>.adoc``), without the extension — the same
    string an ``xref:`` in the docs would use. An anchor may be appended with
    ``#``. Turning a page into a URL belongs to the edge, not here: see
    ``shvatka.common.docs.DocsUrlFactory``.
    """

    AUTH = "player/auth"
    JOIN_TEAM = "player/join_team"
    LEAVE_TEAM = "player/leave_team"
    PLAY = "player/play"
    PLAY_KEYS = "player/play#keys"
    PROMOTION = "player/promotion"

    CREATE_CHAT = "setup_team/create_chat"
    GROUP_TO_SUPERGROUP = "setup_team/group2sg"
    CHECK_CHAT = "setup_team/check_is_sg"
    CREATE_TEAM = "setup_team/create_team"
    ADD_PLAYERS = "setup_team/add_players"
    MANAGE_TEAM = "setup_team/manage_team"
    TEAM_PERMISSIONS = "setup_team/permissions"
    CHANGE_CAPTAIN = "setup_team/change_captain"
    WAIVERS = "setup_team/waivers"
    MOVE_CHAT = "setup_team/move_chat"

    LEVEL_CONCEPT = "author/level-concept"
    GAME_CREATE = "author/game-create"
    LEVEL_CREATE = "author/level-create"
    GAME_LEVELS = "author/game-levels"
    GAME_SCHEDULE = "author/game-schedule"
    GAME_ORGS = "author/game-orgs"

    SPY = "org/spy"

    @property
    def nav_title(self) -> str:
        """The page title, as the docs navigation names it (in Russian).

        Not ``title`` — ``str`` already has one, and shadowing it would change
        what ``"...".title()`` means for every DocPage.
        """
        return DOC_PAGE_TITLES[self]


DOC_PAGE_TITLES: dict[DocPage, str] = {
    DocPage.AUTH: "Вход",
    DocPage.JOIN_TEAM: "Как вступить в команду",
    DocPage.LEAVE_TEAM: "Как выйти из команды",
    DocPage.PLAY: "Как играть",
    DocPage.PLAY_KEYS: "Ввод ключей",
    DocPage.PROMOTION: "Аппрув",
    DocPage.CREATE_CHAT: "Создать чат",
    DocPage.GROUP_TO_SUPERGROUP: "Преобразовать чат в супергруппу",
    DocPage.CHECK_CHAT: "Проверить чат",
    DocPage.CREATE_TEAM: "Создание команды",
    DocPage.ADD_PLAYERS: "Добавить игроков",
    DocPage.MANAGE_TEAM: "Управление командой",
    DocPage.TEAM_PERMISSIONS: "Полномочия в команде",
    DocPage.CHANGE_CAPTAIN: "Передача капитанства",
    DocPage.WAIVERS: "Вейверы",
    DocPage.MOVE_CHAT: "Перенести команду в другой чат",
    DocPage.LEVEL_CONCEPT: "Введение в описание уровня",
    DocPage.GAME_CREATE: "Как создать игру",
    DocPage.LEVEL_CREATE: "Как написать уровень",
    DocPage.GAME_LEVELS: "Как добавить уровни в игру",
    DocPage.GAME_SCHEDULE: "Как запланировать игру",
    DocPage.GAME_ORGS: "Организаторы игры",
    DocPage.SPY: "Как шпионить за игрой",
}
