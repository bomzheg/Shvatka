"""
Планировщик просыпается чуть позже назначенного времени. Если это «чуть позже»
становится началом следующего уровня, оно копится: после десятка уровней команды,
которые весь путь прошли по таймеру, финишируют с разбросом в секунду и больше.
Здесь проверяем, что и уровни, и подсказки отсчитываются от записанного начала
уровня, а не от момента пробуждения планировщика.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from shvatka.core.games.game_play import calculate_hint_time, send_hint
from shvatka.core.models import dto
from shvatka.core.models.dto import action, hints, scn
from shvatka.core.models.enums import GameStatus
from shvatka.core.services.key import calculate_timer_level_up_time
from shvatka.core.views.game import ShowTasks, ViewSender
from tests.mocks.scheduler_mock import SchedulerMock

LEVEL_STARTED_AT = datetime(2025, 4, 12, 22, 0, tzinfo=UTC)
LEVEL_UP_EFFECTS = action.Effects(id=uuid.uuid4(), level_up=True)
BONUS_EFFECTS = action.Effects(id=uuid.uuid4(), bonus_minutes=1)


def create_player(id_: int = 1) -> dto.Player:
    return dto.Player(id=id_, can_be_author=False, is_dummy=False, username=f"player{id_}")


def create_team(id_: int = 1) -> dto.Team:
    return dto.Team(id=id_, name=f"team {id_}", captain=None, is_dummy=False, description=None)


def create_game(id_: int = 1) -> dto.Game:
    return dto.Game(
        id=id_,
        author=create_player(100),
        name=f"game {id_}",
        status=GameStatus.started,
        manage_token="",
        start_at=LEVEL_STARTED_AT,
        number=id_,
        results=dto.GameResults(
            published_chanel_id=None, results_picture_file_id=None, keys_url=None
        ),
    )


def create_level(timer_minutes: int = 30) -> dto.Level:
    return dto.Level(
        db_id=1,
        name_id="timed",
        author=create_player(100),
        scenario=scn.LevelScenario(
            id="timed",
            time_hints=scn.HintsList(
                [
                    hints.TimeHint(time=0, hint=[hints.TextHint(text="puzzle")]),
                    hints.TimeHint(time=5, hint=[hints.TextHint(text="first")]),
                    hints.TimeHint(time=12, hint=[hints.TextHint(text="second")]),
                ]
            ),
            conditions=scn.Conditions(
                [
                    action.LevelTimerEffectsCondition(
                        action_time=timer_minutes,
                        effects=LEVEL_UP_EFFECTS,
                    ),
                    action.KeyEffectsCondition(keys={"SHB1"}, effects=BONUS_EFFECTS),
                ]
            ),
            __model_version__=1,
        ),
        game_id=1,
        number_in_game=0,
    )


def create_level_time(id_: int = 7, start_at: datetime = LEVEL_STARTED_AT) -> dto.LevelTime:
    return dto.LevelTime(
        id=id_,
        game=create_game(),
        team=create_team(),
        level_number=0,
        start_at=start_at,
    )


def test_level_up_time_is_when_timer_was_due():
    level = create_level(timer_minutes=30)
    # планировщик проснулся на 300 мс позже, чем должен был
    now = LEVEL_STARTED_AT + timedelta(minutes=30, milliseconds=300)

    actual = calculate_timer_level_up_time(
        lvl=level, effects=LEVEL_UP_EFFECTS, started_at=LEVEL_STARTED_AT, now=now
    )

    assert actual == LEVEL_STARTED_AT + timedelta(minutes=30)


def test_level_up_time_is_not_in_future():
    """Страховка: записанное время окончания уровня не должно опережать реальное."""
    level = create_level(timer_minutes=30)
    now = LEVEL_STARTED_AT + timedelta(minutes=10)

    actual = calculate_timer_level_up_time(
        lvl=level, effects=LEVEL_UP_EFFECTS, started_at=LEVEL_STARTED_AT, now=now
    )

    assert actual == now


def test_level_up_time_falls_back_to_now_for_unknown_effects():
    level = create_level(timer_minutes=30)
    now = LEVEL_STARTED_AT + timedelta(minutes=30, milliseconds=300)

    actual = calculate_timer_level_up_time(
        lvl=level,
        effects=action.Effects(id=uuid.uuid4(), level_up=True),
        started_at=LEVEL_STARTED_AT,
        now=now,
    )

    assert actual == now


def test_timer_level_ups_do_not_accumulate_delay():
    """Двенадцать уровней по таймеру — финиш ровно через сумму таймеров."""
    level = create_level(timer_minutes=30)
    started_at = LEVEL_STARTED_AT
    for i in range(12):
        # каждое пробуждение планировщика опаздывает на свои полсекунды
        now = started_at + timedelta(minutes=30, milliseconds=100 * (i % 5) + 50)
        started_at = calculate_timer_level_up_time(
            lvl=level, effects=LEVEL_UP_EFFECTS, started_at=started_at, now=now
        )

    assert started_at == LEVEL_STARTED_AT + timedelta(minutes=30 * 12)


def test_get_timer_action_time():
    scenario = create_level(timer_minutes=42).scenario

    assert scenario.get_timer_action_time(LEVEL_UP_EFFECTS.id) == timedelta(minutes=42)
    assert scenario.get_timer_action_time(BONUS_EFFECTS.id) is None
    assert scenario.get_timer_action_time(uuid.uuid4()) is None


def test_calculate_hint_time_counts_from_level_start():
    hint = hints.TimeHint(time=12, hint=[hints.TextHint(text="second")])

    assert calculate_hint_time(LEVEL_STARTED_AT, hint) == LEVEL_STARTED_AT + timedelta(minutes=12)


class LevelTimeGetterStub:
    def __init__(self, level_time: dto.LevelTime) -> None:
        self.level_time = level_time

    async def get_current_level_time(self, team: dto.Team, game: dto.Game) -> dto.LevelTime:
        return self.level_time


class ViewSenderStub(ViewSender):
    def __init__(self) -> None:
        self.tasks: list[ShowTasks] = []

    async def show_later(self, tasks: ShowTasks) -> None:
        self.tasks.append(tasks)


@pytest.mark.asyncio
async def test_next_hint_is_planned_from_level_start():
    """Подсказка, отправленная с опозданием, не сдвигает следующую."""
    level = create_level()
    level_time = create_level_time()
    scheduler = SchedulerMock()

    await send_hint(
        level=level,
        lt_id=level_time.id,
        hint_number=1,
        team=create_team(),
        game=create_game(),
        dao=LevelTimeGetterStub(level_time),
        sender=ViewSenderStub(),
        scheduler=scheduler,
    )

    assert len(scheduler.plain_hint_calls) == 1
    *_, hint_number, lt_id, run_at = scheduler.plain_hint_calls[0]
    assert hint_number == 2
    assert lt_id == level_time.id
    assert run_at == LEVEL_STARTED_AT + timedelta(minutes=12)
