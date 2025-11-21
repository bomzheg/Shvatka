import logging
from datetime import datetime

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.base import JobLookupError
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dishka import AsyncContainer

from shvatka.core.interfaces.scheduler import Scheduler, LevelTestScheduler
from shvatka.core.models import dto
from shvatka.core.models.dto import action
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.config.models.db import RedisConfig
from shvatka.infrastructure.scheduler.context import ScheduledContextHolder

logger = logging.getLogger(__name__)


class ApScheduler(Scheduler, LevelTestScheduler):
    def __init__(self, dishka: AsyncContainer, redis_config: RedisConfig) -> None:
        ScheduledContextHolder.dishka = dishka
        self.dishka = dishka
        self.job_store = RedisJobStore(
            jobs_key="SH.jobs",
            run_times_key="SH.run_times",
            host=redis_config.url,
            port=redis_config.port,
            db=redis_config.db,
        )
        self.executor = AsyncIOExecutor()
        job_defaults = {
            "coalesce": False,
            "max_instances": 20,
            "misfire_grace_time": 3600,
        }
        logger.info("configuring shedulder...")
        self.scheduler = AsyncIOScheduler(
            jobstores={"default": self.job_store},
            job_defaults=job_defaults,
            executors={"default": self.executor},
        )

    async def plain_prepare(self, game: dto.Game):
        self.scheduler.add_job(
            func="shvatka.infrastructure.scheduler.wrappers:prepare_game_wrapper",
            kwargs={"game_id": game.id, "author_id": game.author.id},
            trigger="date",
            run_date=game.prepared_at.astimezone(tz=tz_utc),
            timezone=tz_utc,
            id=_prepare_game_key(game),
            name="plaint_prepare_game",
        )

    async def plain_start(self, game: dto.Game):
        assert game.start_at
        self.scheduler.add_job(
            func="shvatka.infrastructure.scheduler.wrappers:start_game_wrapper",
            kwargs={"game_id": game.id, "author_id": game.author.id},
            trigger="date",
            run_date=game.start_at.astimezone(tz=tz_utc),
            timezone=tz_utc,
            id=_start_game_key(game),
            name="plain_start",
        )

    async def cancel_scheduled_game(self, game: dto.Game):
        try:
            self.scheduler.remove_job(job_id=_prepare_game_key(game))
        except JobLookupError as e:
            logger.error(
                "can't remove job %s for preparing game %s",
                _prepare_game_key(game),
                game.id,
                exc_info=e,
            )
        try:
            self.scheduler.remove_job(job_id=_start_game_key(game))
        except JobLookupError as e:
            logger.error(
                "can't remove job %s for start game %s", _start_game_key(game), game.id, exc_info=e
            )

    async def plain_hint(
        self,
        level: dto.Level,
        team: dto.Team,
        hint_number: int,
        lt_id: int,
        run_at: datetime,
    ):
        self.scheduler.add_job(
            func="shvatka.infrastructure.scheduler.wrappers:send_hint_wrapper",
            kwargs={
                "level_id": level.db_id,
                "team_id": team.id,
                "hint_number": hint_number,
                "lt_id": lt_id,
            },
            trigger="date",
            run_date=run_at,
            timezone=tz_utc,
            name="plain_hint",
        )

    async def plain_level_event(
        self,
        team: dto.Team,
        lt_id: int,
        effects: action.Effects,
        run_at: datetime,
    ):
        self.scheduler.add_job(
            func="shvatka.infrastructure.scheduler.wrappers:event_wrapper",
            kwargs={
                "team_id": team.id,
                "started_level_time_id": lt_id,
            },
            trigger="date",
            run_date=run_at,
            timezone=tz_utc,
            name=f"effects_{team.id}_{effects.id}",
        )

    async def plain_test_hint(
        self,
        suite: dto.LevelTestSuite,
        hint_number: int,
        run_at: datetime,
    ):
        self.scheduler.add_job(
            func="shvatka.infrastructure.scheduler.wrappers:send_hint_for_testing_wrapper",
            kwargs={
                "level_id": suite.level.db_id,
                "game_id": suite.level.game_id,
                "player_id": suite.tester.player.id,
                "hint_number": hint_number,
            },
            trigger="date",
            run_date=run_at,
            timezone=tz_utc,
            name="plain_test_hint",
        )

    async def start(self):
        self.scheduler.start()

    async def close(self):
        self.scheduler.shutdown()
        self.executor.shutdown()
        self.job_store.shutdown()


def _prepare_game_key(game: dto.Game) -> str:
    return f"game-{game.id}-prepare"


def _start_game_key(game: dto.Game) -> str:
    return f"game-{game.id}-start"
