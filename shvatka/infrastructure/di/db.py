from typing import AsyncIterable

from dishka import Provider, Scope, provide, AnyOf
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, AsyncEngine

from shvatka.core.interfaces.dal.waiver import GameWaiversGetter
from shvatka.infrastructure.db import dao
from shvatka.infrastructure.db.config.models.db import DBConfig, RedisConfig
from shvatka.infrastructure.db.dao import (
    GameDao,
    UserDao,
    ChatDao,
    LevelDao,
    LevelTimeDao,
    KeyTimeDao,
    OrganizerDao,
    PlayerDao,
    TeamPlayerDao,
    TeamDao,
    WaiverDao,
    PollDao,
    SecureInvite,
)
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.db.dao.memory.level_testing import LevelTestingData
from shvatka.infrastructure.db.dao.rdb import ForumUserDAO
from shvatka.infrastructure.db.dao.rdb.achievement import AchievementDAO
from shvatka.infrastructure.db.dao.rdb.forum_team import ForumTeamDAO
from shvatka.infrastructure.db.factory import create_engine, create_session_maker, create_redis


class DbProvider(Provider):
    scope = Scope.APP

    def __init__(self):
        super().__init__()
        self.level_test = LevelTestingData()

    @provide
    async def get_engine(self, db_config: DBConfig) -> AsyncIterable[AsyncEngine]:
        engine = create_engine(db_config)
        yield engine
        await engine.dispose(True)

    @provide
    def get_pool(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return create_session_maker(engine)

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self, pool: async_sessionmaker[AsyncSession]
    ) -> AsyncIterable[AsyncSession]:
        async with pool() as session:
            yield session

    @provide
    def get_level_test_data(self) -> LevelTestingData:
        return self.level_test


class DAOProvider(Provider):
    scope = Scope.REQUEST

    @provide
    async def get_dao(
        self, session: AsyncSession, redis: Redis, level_test: LevelTestingData
    ) -> HolderDao:
        return HolderDao(session=session, redis=redis, level_test=level_test)

    @provide
    async def get_game_dao(self, holder: HolderDao) -> dao.GameDao:
        return holder.game

    @provide
    def get_file_info_dao(self, holder: HolderDao) -> dao.FileInfoDao:
        return holder.file_info

    @provide
    def get_timers(self, holder: HolderDao) -> dao.TimersDAO:
        return holder.timers

    @provide
    def user_dao(self, holder: HolderDao) -> dao.UserDao:
        return holder.user

    @provide
    def chat_dao(self, holder: HolderDao) -> dao.ChatDao:
        return holder.chat

    @provide
    def level_dao(self, holder: HolderDao) -> dao.LevelDao:
        return holder.level

    @provide
    def level_time_dao(self, holder: HolderDao) -> dao.LevelTimeDao:
        return holder.level_time

    @provide
    def key_time_dao(self, holder: HolderDao) -> dao.KeyTimeDao:
        return holder.key_time

    @provide
    def organizer_dao(self, holder: HolderDao) -> dao.OrganizerDao:
        return holder.organizer

    @provide
    def player_dao(self, holder: HolderDao) -> dao.PlayerDao:
        return holder.player

    @provide
    def team_player_dao(self, holder: HolderDao) -> dao.TeamPlayerDao:
        return holder.team_player

    @provide
    def team_dao(self, holder: HolderDao) -> dao.TeamDao:
        return holder.team

    @provide(provides=AnyOf[WaiverDao, GameWaiversGetter])
    def waiver_dao(self, holder: HolderDao) -> dao.WaiverDao:
        return holder.waiver

    @provide
    def achievement_dao(self, holder: HolderDao) -> dao.AchievementDAO:
        return holder.achievement

    @provide
    def forum_user_dao(self, holder: HolderDao) -> dao.ForumUserDAO:
        return holder.forum_user

    @provide
    def forum_team_dao(self, holder: HolderDao) -> dao.ForumTeamDAO:
        return holder.forum_team

    @provide
    def poll_dao(self, holder: HolderDao) -> dao.PollDao:
        return holder.poll

    @provide
    def secure_invite_dao(self, holder: HolderDao) -> dao.SecureInvite:
        return holder.secure_invite


class RedisProvider(Provider):
    scope = Scope.APP

    @provide
    async def get_redis(self, config: RedisConfig) -> AsyncIterable[Redis]:
        async with create_redis(config) as redis:
            yield redis
