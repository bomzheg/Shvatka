from typing import AsyncIterable

from dishka import Provider, Scope, provide
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, AsyncEngine

from shvatka.infrastructure.db.config.models.db import DBConfig, RedisConfig
from shvatka.infrastructure.db.dao import (
    FileInfoDao,
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
    def file_info_dao(self, dao: HolderDao) -> FileInfoDao:
        return dao.file_info

    @provide
    def user_dao(self, dao: HolderDao) -> UserDao:
        return dao.user

    @provide
    def chat_dao(self, dao: HolderDao) -> ChatDao:
        return dao.chat

    @provide
    def game_dao(self, dao: HolderDao) -> GameDao:
        return dao.game

    @provide
    def level_dao(self, dao: HolderDao) -> LevelDao:
        return dao.level

    @provide
    def level_time_dao(self, dao: HolderDao) -> LevelTimeDao:
        return dao.level_time

    @provide
    def key_time_dao(self, dao: HolderDao) -> KeyTimeDao:
        return dao.key_time

    @provide
    def organizer_dao(self, dao: HolderDao) -> OrganizerDao:
        return dao.organizer

    @provide
    def player_dao(self, dao: HolderDao) -> PlayerDao:
        return dao.player

    @provide
    def team_player_dao(self, dao: HolderDao) -> TeamPlayerDao:
        return dao.team_player

    @provide
    def team_dao(self, dao: HolderDao) -> TeamDao:
        return dao.team

    @provide
    def waiver_dao(self, dao: HolderDao) -> WaiverDao:
        return dao.waiver

    @provide
    def achievement_dao(self, dao: HolderDao) -> AchievementDAO:
        return dao.achievement

    @provide
    def forum_user_dao(self, dao: HolderDao) -> ForumUserDAO:
        return dao.forum_user

    @provide
    def forum_team_dao(self, dao: HolderDao) -> ForumTeamDAO:
        return dao.forum_team

    @provide
    def poll_dao(self, dao: HolderDao) -> PollDao:
        return dao.poll

    @provide
    def secure_invite_dao(self, dao: HolderDao) -> SecureInvite:
        return dao.secure_invite


class RedisProvider(Provider):
    scope = Scope.APP

    @provide
    async def get_redis(self, config: RedisConfig) -> AsyncIterable[Redis]:
        async with create_redis(config) as redis:
            yield redis
