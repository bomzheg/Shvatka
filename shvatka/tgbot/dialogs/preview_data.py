"""Static data for rendering dialogs without a database.

Every window with a getter needs a matching ``preview_data``: in preview mode
the real getter is never called, so a window without it renders against an
empty dict and usually just blows up on the first missing key.
"""

from datetime import datetime, timedelta
from uuid import UUID

from aiogram.fsm.state import State
from aiogram_dialog.widgets.kbd import Start, SwitchTo
from aiogram_dialog.widgets.text import Const

from shvatka.core.models import dto, enums
from shvatka.core.models.dto import action, hints
from shvatka.core.models.dto.scn.level import Conditions, HintsList, LevelScenario
from shvatka.core.models.enums import GameStatus
from shvatka.core.models.enums.played import Played
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.views.texts import PERMISSION_EMOJI

PREVIEW_NOW = datetime(2024, 5, 18, 18, 0, tzinfo=tz_utc)

PREVIEW_USER = dto.User(
    db_id=5,
    tg_id=900,
    username="bomzheg",
    first_name="Yuriy",
)

PREVIEW_AUTHOR = dto.Player(
    id=1,
    user=PREVIEW_USER,
    username="bomzheg",
    can_be_author=True,
    is_dummy=False,
)

PREVIEW_PLAYER = dto.Player(
    id=2,
    user=dto.User(
        db_id=6,
        tg_id=901,
        username="rainbow_dash",
        first_name="Rainbow",
        last_name="Dash",
    ),
    username="rainbow_dash",
    can_be_author=False,
    is_dummy=False,
)

PREVIEW_PLAYER_WITH_STAT = PREVIEW_AUTHOR.with_stat(
    typed_keys_count=350,
    typed_correct_keys_count=280,
)

PREVIEW_FORUM_USER = dto.ForumUser(
    db_id=7,
    forum_id=6767,
    name="bomzheg",
    registered=PREVIEW_NOW.date(),
    player_id=PREVIEW_AUTHOR.id,
)

PREVIEW_FORUM_TEAM = dto.ForumTeam(
    id=3,
    forum_id=42,
    name="Пони",
    url="http://www.shvatka.ru/index.php?showtopic=42",
)
PREVIEW_FORUM_TEAMS = [PREVIEW_FORUM_TEAM]

PREVIEW_TEAM = dto.Team(
    id=1,
    name="Пони",
    captain=PREVIEW_AUTHOR,
    is_dummy=False,
    description="Дружба - это чудо",
    chat=dto.Chat(
        db_id=11,
        tg_id=-100123456,
        type=enums.ChatType.supergroup,
        title="Пони",
    ),
)

PREVIEW_ANOTHER_TEAM = dto.Team(
    id=2,
    name="Дискорд",
    captain=PREVIEW_PLAYER,
    is_dummy=False,
    description=None,
)

PREVIEW_TEAMS = [PREVIEW_TEAM, PREVIEW_ANOTHER_TEAM]


def _preview_team_player(
    id_: int,
    player: dto.Player,
    role: str,
    emoji: str,
    team: dto.Team = PREVIEW_TEAM,
    joined_days_ago: int = 365,
    left_days_ago: int | None = None,
) -> dto.FullTeamPlayer:
    return dto.FullTeamPlayer(
        id=id_,
        player_id=player.id,
        team_id=team.id,
        date_joined=PREVIEW_NOW - timedelta(days=joined_days_ago),
        date_left=None if left_days_ago is None else PREVIEW_NOW - timedelta(days=left_days_ago),
        role=role,
        emoji=emoji,
        _can_manage_waivers=True,
        _can_manage_players=True,
        _can_change_team_name=True,
        _can_add_players=True,
        _can_remove_players=True,
        player=player,
        team=team,
    )


PREVIEW_TEAM_PLAYER = _preview_team_player(1, PREVIEW_AUTHOR, "Капитан", "👑")
PREVIEW_SELECTED_TEAM_PLAYER = _preview_team_player(2, PREVIEW_PLAYER, "Пилот", "✈️")
PREVIEW_TEAM_PLAYERS = [PREVIEW_TEAM_PLAYER, PREVIEW_SELECTED_TEAM_PLAYER]
PREVIEW_LEFT_TEAM_PLAYER = _preview_team_player(
    3,
    PREVIEW_AUTHOR,
    "Пилот",
    "✈️",
    team=PREVIEW_ANOTHER_TEAM,
    joined_days_ago=730,
    left_days_ago=365,
)
PREVIEW_TEAMS_HISTORY = [PREVIEW_LEFT_TEAM_PLAYER, PREVIEW_TEAM_PLAYER]
PREVIEW_PERMISSIONS = {
    permission.name: PERMISSION_EMOJI[value]
    for permission, value in PREVIEW_SELECTED_TEAM_PLAYER.permissions.items()
}

PREVIEW_PLAYER_STAT = {
    "player": PREVIEW_PLAYER_WITH_STAT,
    "correct_keys": (
        PREVIEW_PLAYER_WITH_STAT.typed_correct_keys_count
        / PREVIEW_PLAYER_WITH_STAT.typed_keys_count
    ),
    "history": PREVIEW_TEAMS_HISTORY,
}

PREVIEW_MY_TEAM = {"team": PREVIEW_TEAM, "team_player": PREVIEW_TEAM_PLAYER}
PREVIEW_TEAM_WITH_PLAYERS = {
    **PREVIEW_MY_TEAM,
    "players": [PREVIEW_SELECTED_TEAM_PLAYER],
}
PREVIEW_SELECTED_TEAM_PLAYER_DATA = {
    **PREVIEW_MY_TEAM,
    "selected_player": PREVIEW_PLAYER,
    "selected_team_player": PREVIEW_SELECTED_TEAM_PLAYER,
    **PREVIEW_PERMISSIONS,
}

PREVIEW_GAME = dto.PreviewGame(
    id=1,
    author=PREVIEW_AUTHOR,
    name="Схватка это чудо",
    start_at=PREVIEW_NOW,
    status=GameStatus.getting_waivers,
    manage_token="1",  # noqa: S106
    results=dto.GameResults(
        published_chanel_id=-100123435,
        results_picture_file_id=None,
        keys_url=None,
    ),
    number=1,
    levels_count=13,
)
PREVIEW_GAMES = [PREVIEW_GAME]

PREVIEW_TEAM_CARD = {
    "team": PREVIEW_TEAM,
    "players": PREVIEW_TEAM_PLAYERS,
    "games": PREVIEW_GAMES,
    "game_numbers": [str(PREVIEW_GAME.number)],
}

PREVIEW_SIMPLE_GAME = dto.Game(
    id=PREVIEW_GAME.id,
    author=PREVIEW_GAME.author,
    name=PREVIEW_GAME.name,
    start_at=PREVIEW_GAME.start_at,
    status=PREVIEW_GAME.status,
    manage_token=PREVIEW_GAME.manage_token,
    results=PREVIEW_GAME.results,
    number=PREVIEW_GAME.number,
)

PREVIEW_ORG = dto.SecondaryOrganizer(
    id=1,
    player=PREVIEW_PLAYER,
    game=PREVIEW_SIMPLE_GAME,
    can_spy=True,
    can_see_log_keys=True,
    can_validate_waivers=False,
    view_scenario=True,
    deleted=False,
)
PREVIEW_ORGS = [PREVIEW_ORG]
PREVIEW_ORG_PERMISSIONS = {
    "can_spy": PERMISSION_EMOJI[PREVIEW_ORG.can_spy],
    "can_see_log_keys": PERMISSION_EMOJI[PREVIEW_ORG.can_see_log_keys],
    "can_validate_waivers": PERMISSION_EMOJI[PREVIEW_ORG.can_validate_waivers],
    "view_scenario": PERMISSION_EMOJI[PREVIEW_ORG.view_scenario],
}

PREVIEW_SPY_ORG = {
    "game": PREVIEW_SIMPLE_GAME,
    "player": PREVIEW_AUTHOR,
    "org": PREVIEW_ORG,
}

PREVIEW_KEYS = {"СХПОНИ", "СХДРУЖБА"}
PREVIEW_HINTS: list[hints.AnyHint] = [
    hints.TextHint(text="Загадка уровня: где живёт Пинки Пай?"),
    hints.GPSHint(latitude=55.75, longitude=37.61),
]
PREVIEW_NUMERATED_HINTS = list(enumerate(PREVIEW_HINTS))
PREVIEW_TIME_HINTS = [
    hints.TimeHint(time=0, hint=[hints.TextHint(text="Загадка уровня")]),
    hints.TimeHint(time=10, hint=[hints.TextHint(text="Подсказка про сахарный дворец")]),
    hints.TimeHint(time=20, hint=[hints.TextHint(text="Совсем простая подсказка")]),
]

PREVIEW_HINTS_DATA = {
    "hints": PREVIEW_HINTS,
    "numerated_hints": PREVIEW_NUMERATED_HINTS,
    "time": 10,
    "has_hints": True,
}

PREVIEW_EFFECTS = action.Effects(
    id=UUID("00000000-0000-0000-0000-000000000001"),
    hints_=[hints.TextHint(text="Бонусная подсказка")],
    bonus_minutes=-5.0,
    level_up=False,
    next_level=None,
)
PREVIEW_ROUTED_EFFECTS = action.Effects(
    id=UUID("00000000-0000-0000-0000-000000000002"),
    hints_=[hints.TextHint(text="Бонусная подсказка")],
    bonus_minutes=-5.0,
    level_up=True,
    next_level="Fluttershy",
)
PREVIEW_TIMER = action.LevelTimerEffectsCondition(action_time=30, effects=PREVIEW_EFFECTS)
PREVIEW_TIMERS = [PREVIEW_TIMER]
PREVIEW_KEY_EFFECTS_CONDITION = action.KeyEffectsCondition(
    keys={"СХБОНУС"},
    effects=PREVIEW_EFFECTS,
)
PREVIEW_EFFECTS_CONDITIONS = list(enumerate([PREVIEW_KEY_EFFECTS_CONDITION]))

PREVIEW_EFFECTS_DATA = {
    "dialog_data": {"effect_id": str(PREVIEW_ROUTED_EFFECTS.id)},
    "bonus_minutes": PREVIEW_ROUTED_EFFECTS.bonus_minutes,
    "level_up": PREVIEW_ROUTED_EFFECTS.level_up,
    "next_level": PREVIEW_ROUTED_EFFECTS.next_level,
    "hints": PREVIEW_ROUTED_EFFECTS.hints_,
    "level_id": "Pinky Pie",
    "game_id": 1,
}

PREVIEW_LEVEL = dto.Level(
    db_id=1,
    name_id="Pinky Pie",
    author=PREVIEW_AUTHOR,
    scenario=LevelScenario(
        id="Pinky Pie",
        time_hints=HintsList(PREVIEW_TIME_HINTS),
        conditions=Conditions([action.KeyWinCondition(PREVIEW_KEYS)]),
        __model_version__=1,
    ),
    game_id=PREVIEW_GAME.id,
    number_in_game=0,
)
PREVIEW_LEVELS = [PREVIEW_LEVEL]
PREVIEW_MANAGED_LEVEL = {
    "level": PREVIEW_LEVEL,
    "time_hints": PREVIEW_TIME_HINTS,
    "org": PREVIEW_ORG,
}

PREVIEW_LEVEL_SCN = {
    "level_id": PREVIEW_LEVEL.name_id,
    "keys": PREVIEW_KEYS,
    "timers": PREVIEW_TIMERS,
    "effects_key": [PREVIEW_KEY_EFFECTS_CONDITION],
    "win_timer": None,
    "time_hints": PREVIEW_TIME_HINTS,
}

PREVIEW_FULL_GAME = PREVIEW_SIMPLE_GAME.to_full_game(
    levels=PREVIEW_LEVELS,  # type: ignore[arg-type]
)

PREVIEW_WAIVERS = {
    PREVIEW_TEAM: [
        dto.VotedPlayer(player=PREVIEW_AUTHOR, pit=PREVIEW_TEAM_PLAYER),
        dto.VotedPlayer(player=PREVIEW_PLAYER, pit=PREVIEW_SELECTED_TEAM_PLAYER),
    ],
}
PREVIEW_VOTE = Played.yes

PREVIEW_LEVEL_TIME = dto.LevelTimeOnGame(
    id=1,
    game=PREVIEW_SIMPLE_GAME,
    team=PREVIEW_TEAM,
    level_number=0,
    start_at=PREVIEW_NOW - timedelta(minutes=17),
    is_finished=False,
    hint=dto.SpyHintInfo(number=1, time=10),
    name_id=PREVIEW_LEVEL.name_id,
)
PREVIEW_FINISHED_LEVEL_TIME = dto.LevelTimeOnGame(
    id=2,
    game=PREVIEW_SIMPLE_GAME,
    team=PREVIEW_ANOTHER_TEAM,
    level_number=1,
    start_at=PREVIEW_NOW - timedelta(minutes=3),
    is_finished=True,
    hint=None,
    name_id=None,
)
PREVIEW_SPY_STAT = {PREVIEW_LEVEL_TIME.level_number: [PREVIEW_LEVEL_TIME]}

TIMES_PRESET = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]


class PreviewStart(Start):
    def __init__(self, state: State) -> None:
        super().__init__(Const(""), "", state)


class PreviewSwitchTo(SwitchTo):
    def __init__(self, state: State) -> None:
        super().__init__(Const(""), "", state)
