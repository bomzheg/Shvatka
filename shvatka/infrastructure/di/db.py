from collections.abc import AsyncIterable

from dishka import AnyOf, Provider, Scope, provide
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from shvatka.core.interfaces.dal.complex import (
    GamePackager,
    GameStatDao,
    TeamMerger,
    TypedKeyGetter,
)
from shvatka.core.interfaces.dal.game import GameCreator, GameUpserter
from shvatka.core.interfaces.dal.game_play import GamePlayerDao, GamePreparer
from shvatka.core.interfaces.dal.level import LevelDeleter
from shvatka.core.interfaces.dal.level_testing import LevelTestingDao
from shvatka.core.interfaces.dal.level_times import GameStarter
from shvatka.core.interfaces.dal.organizer import OrgAdder, OrgByPlayerGetter
from shvatka.core.interfaces.dal.player import PlayerPromoter, PlayerTeamChecker, TeamLeaver
from shvatka.core.interfaces.dal.team import TeamCreator
from shvatka.core.interfaces.dal.waiver import GameWaiversGetter, WaiverApprover, WaiverGetter
from shvatka.core.notifications.adapters import (
    NotificationMarker,
    NotificationReader,
    NotificationWriter,
    RequestStorage,
)
from shvatka.core.players.interfaces import PlayerMerger
from shvatka.core.teams.adapters import ChatlessTeamCreator
from shvatka.infrastructure.db import dao
from shvatka.infrastructure.db.config.models.db import DBConfig, RedisConfig
from shvatka.infrastructure.db.dao import (
    WaiverDao,
)
from shvatka.infrastructure.db.dao.complex.game import (
    GameCreatorImpl,
    GamePackagerImpl,
    GameUpserterImpl,
    LevelDeleterImpl,
)
from shvatka.infrastructure.db.dao.complex.game_play import (
    GamePlayerDaoImpl,
    GamePreparerImpl,
    GameStarterImpl,
)
from shvatka.infrastructure.db.dao.complex.key_log import TypedKeyGetterImpl
from shvatka.infrastructure.db.dao.complex.level_testing import LevelTestComplex
from shvatka.infrastructure.db.dao.complex.level_times import GameStatImpl
from shvatka.infrastructure.db.dao.complex.orgs import OrgAdderImpl
from shvatka.infrastructure.db.dao.complex.player import PlayerMergerImpl, PlayerPromoterImpl
from shvatka.infrastructure.db.dao.complex.team import (
    TeamCreatorImpl,
    TeamLeaverImpl,
    TeamMergerImpl,
)
from shvatka.infrastructure.db.dao.complex.waiver import WaiverApproverImpl
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.db.dao.memory.level_testing import LevelTestingData
from shvatka.infrastructure.db.factory import create_engine, create_redis, create_session_maker


class DbProvider(Provider):
    scope = Scope.APP

    def __init__(self) -> None:
        super().__init__()
        self.level_test = LevelTestingData()

    @provide
    async def get_engine(self, db_config: DBConfig) -> AsyncIterable[AsyncEngine]:
        engine = create_engine(db_config)
        yield engine
        await engine.dispose(close=True)

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

    @provide(provides=AnyOf[dao.OrganizerDao, OrgByPlayerGetter])
    def organizer_dao(self, holder: HolderDao) -> dao.OrganizerDao:
        return holder.organizer

    @provide
    def player_dao(self, holder: HolderDao) -> dao.PlayerDao:
        return holder.player

    @provide(
        provides=AnyOf[
            dao.TeamPlayerDao,
            PlayerTeamChecker,
        ]
    )
    def team_player_dao(self, holder: HolderDao) -> dao.TeamPlayerDao:
        return holder.team_player

    @provide
    def team_dao(self, holder: HolderDao) -> dao.TeamDao:
        return holder.team

    @provide(provides=AnyOf[WaiverDao, GameWaiversGetter, WaiverGetter])
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

    @provide
    def pinned_message_dao(self, redis: Redis) -> dao.PinnedMessageDao:
        return dao.PinnedMessageDao(redis=redis)

    @provide
    async def push_subscription_dao(
        self, pool: async_sessionmaker[AsyncSession]
    ) -> AsyncIterable[dao.PushSubscriptionDAO]:
        async with pool() as session:
            yield dao.PushSubscriptionDAO(session=session)

    @provide
    def notification_dao(
        self, session: AsyncSession
    ) -> AnyOf[dao.NotificationDAO, NotificationReader, NotificationMarker, NotificationWriter]:
        return dao.NotificationDAO(session=session)

    @provide
    def action_request_dao(
        self, session: AsyncSession
    ) -> AnyOf[dao.ActionRequestDAO, RequestStorage]:
        return dao.ActionRequestDAO(session=session)


class ComplexDaoProvider(Provider):
    """Daos composed over several tables — one narrow Protocol each, built from HolderDao."""

    scope = Scope.REQUEST

    level_deleter = provide(LevelDeleterImpl, provides=LevelDeleter)
    waiver_approver = provide(WaiverApproverImpl, provides=WaiverApprover)
    game_upserter = provide(GameUpserterImpl, provides=GameUpserter)
    game_creator = provide(GameCreatorImpl, provides=GameCreator)
    game_packager = provide(GamePackagerImpl, provides=GamePackager)
    game_preparer = provide(GamePreparerImpl, provides=GamePreparer)
    game_starter = provide(GameStarterImpl, provides=GameStarter)
    game_player = provide(GamePlayerDaoImpl, provides=GamePlayerDao)
    game_stat = provide(GameStatImpl, provides=GameStatDao)
    typed_keys = provide(TypedKeyGetterImpl, provides=TypedKeyGetter)
    level_testing = provide(LevelTestComplex, provides=LevelTestingDao)
    org_adder = provide(OrgAdderImpl, provides=OrgAdder)
    player_promoter = provide(PlayerPromoterImpl, provides=PlayerPromoter)
    player_merger = provide(PlayerMergerImpl, provides=PlayerMerger)
    team_creator = provide(TeamCreatorImpl, provides=AnyOf[TeamCreator, ChatlessTeamCreator])
    team_leaver = provide(TeamLeaverImpl, provides=TeamLeaver)
    team_merger = provide(TeamMergerImpl, provides=TeamMerger)


class RedisProvider(Provider):
    scope = Scope.APP

    @provide
    async def get_redis(self, config: RedisConfig) -> AsyncIterable[Redis]:
        async with create_redis(config) as redis:
            yield redis
