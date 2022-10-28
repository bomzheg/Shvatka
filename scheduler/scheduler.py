import logging
from datetime import datetime

from aiogram import Bot
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from redis import Redis
from sqlalchemy.orm import sessionmaker

from db.config.models.db import RedisConfig
from scheduler.context import ScheduledContextHolder
from scheduler.wrappers import prepare_game_wrapper, start_game_wrapper, send_hint_wrapper
from shvatka.models import dto
from shvatka.scheduler import Scheduler
from shvatka.utils.datetime_utils import tz_utc

logger = logging.getLogger(__name__)


class ApScheduler(Scheduler):
    def __init__(
        self,
        redis_config: RedisConfig,
        pool: sessionmaker,
        redis: Redis,
        bot: Bot = None,
        game_log_chat: int = None,
    ):
        ScheduledContextHolder.poll = pool
        ScheduledContextHolder.redis = redis
        ScheduledContextHolder.bot = bot
        ScheduledContextHolder.scheduler = self
        ScheduledContextHolder.game_log_chat = game_log_chat
        self.job_store = RedisJobStore(
            jobs_key="SH.jobs",
            run_times_key="SH.run_times",
            host=redis_config.url,
            port=redis_config.port,
            db=redis_config.db,
        )
        self.executor = AsyncIOExecutor()
        job_defaults = {
            'coalesce': False,
            'max_instances': 20,
            'misfire_grace_time': 3600,
        }
        logger.info("configuring shedulder...")
        self.scheduler = AsyncIOScheduler(
            jobstores={'default': self.job_store},
            job_defaults=job_defaults,
            executors={'default': self.executor},
        )

    async def plain_prepare(self, game: dto.Game):
        self.scheduler.add_job(
            func=prepare_game_wrapper,
            kwargs={"game_id": game.id, "author_id": game.author.id},
            trigger='date',
            run_date=game.prepared_at.astimezone(tz=tz_utc),
            timezone=tz_utc,
        )

    async def plain_start(self, game: dto.Game):
        self.scheduler.add_job(
            func=start_game_wrapper,
            kwargs={"game_id": game.id, "author_id": game.author.id},
            trigger='date',
            run_date=game.start_at.astimezone(tz=tz_utc),
            timezone=tz_utc,
        )

    async def plain_hint(
        self, level: dto.Level, team: dto.Team, hint_number: int, run_at: datetime,
    ):
        self.scheduler.add_job(
            func=send_hint_wrapper,
            kwargs={"level_id": level.db_id, "team_id": team.id, "hint_number": hint_number},
            trigger='date',
            run_date=run_at,
            timezone=tz_utc,
        )

    async def start(self):
        self.scheduler.start()

    async def close(self):
        self.scheduler.shutdown()
        self.executor.shutdown()
        self.job_store.shutdown()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
