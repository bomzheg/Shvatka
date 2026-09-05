import typing
from datetime import datetime, tzinfo

from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from .memory.level_testing import LevelTestingData
from .rdb import (
    ChatDao,
    EmailAccountDao,
    FileInfoDao,
    ForumUserDAO,
    GameDao,
    GameFileDao,
    KeyTimeDao,
    LevelDao,
    LevelFileDao,
    LevelTimeDao,
    OrganizerDao,
    PlayerDao,
    TeamDao,
    TeamPlayerDao,
    UserDao,
    WaiverDao,
)
from .rdb.achievement import AchievementDAO
from .rdb.events import GameEventDao
from .rdb.forum_team import ForumTeamDAO
from .rdb.timers import TimersDAO
from .redis import EmailConfirmationStore, OneTimeToken, PollDao, RateLimiter, SecureInvite


class HolderDao:
    def __init__(
        self,
        session: AsyncSession,
        redis: Redis,
        level_test: LevelTestingData,
        clock: typing.Callable[[tzinfo], datetime] = datetime.now,
    ) -> None:
        self.session = session
        self.clock = clock
        self.user = UserDao(self.session, clock=clock)
        self.chat = ChatDao(self.session, clock=clock)
        self.file_info = FileInfoDao(self.session, clock=clock)
        self.game = GameDao(self.session, clock=clock)
        self.game_file = GameFileDao(self.session, clock=clock)
        self.level = LevelDao(self.session, clock=clock)
        self.level_file = LevelFileDao(self.session, clock=clock)
        self.level_time = LevelTimeDao(self.session, clock=clock)
        self.key_time = KeyTimeDao(self.session, clock=clock)
        self.organizer = OrganizerDao(self.session, clock=clock)
        self.player = PlayerDao(self.session, clock=clock)
        self.email = EmailAccountDao(self.session, clock=clock)
        self.team_player = TeamPlayerDao(self.session, clock=clock)
        self.team = TeamDao(self.session, clock=clock)
        self.waiver = WaiverDao(self.session, clock=clock)
        self.achievement = AchievementDAO(self.session, clock=clock)
        self.forum_user = ForumUserDAO(self.session, clock=clock)
        self.forum_team = ForumTeamDAO(self.session, clock=clock)
        self.events = GameEventDao(self.session, clock=clock)
        self.timers = TimersDAO(self.session, clock=clock)
        self.poll = PollDao(redis=redis, clock=clock)
        self.secure_invite = SecureInvite(redis=redis, clock=clock)
        self.one_time_token = OneTimeToken(redis=redis, clock=clock)
        self.email_confirm = EmailConfirmationStore(redis=redis, clock=clock)
        self.rate_limiter = RateLimiter(redis=redis)
        self.level_test = level_test

    async def commit(self):
        await self.session.commit()
