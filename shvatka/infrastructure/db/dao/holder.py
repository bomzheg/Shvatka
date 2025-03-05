import typing
from datetime import datetime, tzinfo

from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.core.interfaces.dal.complex import (
    TeamMerger,
    TypedKeyGetter,
    GameStatDao,
    GamePackager,
)
from shvatka.core.interfaces.dal.game import GameUpserter, GameCreator
from shvatka.core.interfaces.dal.game_play import GamePreparer, GamePlayerDao
from shvatka.core.interfaces.dal.level_testing import LevelTestingDao
from shvatka.core.interfaces.dal.level_times import GameStarter
from shvatka.core.interfaces.dal.organizer import OrgAdder
from shvatka.core.interfaces.dal.player import TeamLeaver, PlayerPromoter, PlayerMerger
from shvatka.core.interfaces.dal.team import TeamCreator
from shvatka.core.interfaces.dal.waiver import WaiverVoteAdder, WaiverVoteGetter, WaiverApprover
from .complex import WaiverVoteAdderImpl, WaiverVoteGetterImpl
from .complex.game import GameUpserterImpl, GameCreatorImpl, GamePackagerImpl
from .complex.game_play import GamePreparerImpl, GameStarterImpl, GamePlayerDaoImpl
from .complex.key_log import TypedKeyGetterImpl
from .complex.level_testing import LevelTestComplex
from .complex.level_times import GameStatImpl
from .complex.orgs import OrgAdderImpl
from .complex.player import PlayerPromoterImpl, PlayerMergerImpl
from .complex.team import TeamCreatorImpl, TeamLeaverImpl, TeamMergerImpl
from .complex.waiver import WaiverApproverImpl
from .memory.level_testing import LevelTestingData
from .rdb import (
    ChatDao,
    UserDao,
    FileInfoDao,
    GameDao,
    LevelDao,
    LevelTimeDao,
    KeyTimeDao,
    OrganizerDao,
    PlayerDao,
    TeamPlayerDao,
    TeamDao,
    WaiverDao,
    ForumUserDAO,
)
from .rdb.achievement import AchievementDAO
from .rdb.forum_team import ForumTeamDAO
from .redis import PollDao, SecureInvite


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
        self.level = LevelDao(self.session, clock=clock)
        self.level_time = LevelTimeDao(self.session, clock=clock)
        self.key_time = KeyTimeDao(self.session, clock=clock)
        self.organizer = OrganizerDao(self.session, clock=clock)
        self.player = PlayerDao(self.session, clock=clock)
        self.team_player = TeamPlayerDao(self.session, clock=clock)
        self.team = TeamDao(self.session, clock=clock)
        self.waiver = WaiverDao(self.session, clock=clock)
        self.achievement = AchievementDAO(self.session, clock=clock)
        self.forum_user = ForumUserDAO(self.session, clock=clock)
        self.forum_team = ForumTeamDAO(self.session, clock=clock)
        self.poll = PollDao(redis=redis, clock=clock)
        self.secure_invite = SecureInvite(redis=redis, clock=clock)
        self.level_test = level_test

    async def commit(self):
        await self.session.commit()

    @property
    def waiver_vote_adder(self) -> WaiverVoteAdder:
        return WaiverVoteAdderImpl(
            poll=self.poll, waiver=self.waiver, team_player=self.team_player
        )

    @property
    def waiver_vote_getter(self) -> WaiverVoteGetter:
        return WaiverVoteGetterImpl(poll=self.poll, player=self.player)

    @property
    def waiver_approver(self) -> WaiverApprover:
        return WaiverApproverImpl(
            poll=self.poll, player=self.player, waiver=self.waiver, team_player=self.team_player
        )

    @property
    def game_upserter(self) -> GameUpserter:
        return GameUpserterImpl(game=self.game, level=self.level, file_info=self.file_info)

    @property
    def game_creator(self) -> GameCreator:
        return GameCreatorImpl(game=self.game, level=self.level)

    @property
    def game_packager(self) -> GamePackager:
        return GamePackagerImpl(dao=self)

    @property
    def team_creator(self) -> TeamCreator:
        return TeamCreatorImpl(dao=self)

    @property
    def team_leaver(self) -> TeamLeaver:
        return TeamLeaverImpl(dao=self)

    @property
    def team_merger(self) -> TeamMerger:
        return TeamMergerImpl(dao=self)

    @property
    def game_preparer(self) -> GamePreparer:
        return GamePreparerImpl(poll=self.poll, waiver=self.waiver, org=self.organizer)

    @property
    def game_starter(self) -> GameStarter:
        return GameStarterImpl(dao=self)

    @property
    def game_player(self) -> GamePlayerDao:
        return GamePlayerDaoImpl(
            level_time=self.level_time,
            level=self.level,
            key_time=self.key_time,
            waiver=self.waiver,
            game=self.game,
            organizer=self.organizer,
        )

    @property
    def org_adder(self) -> OrgAdder:
        return OrgAdderImpl(
            game=self.game, organizer=self.organizer, secure_invite=self.secure_invite
        )

    @property
    def player_promoter(self) -> PlayerPromoter:
        return PlayerPromoterImpl(dao=self)

    @property
    def player_merger(self) -> PlayerMerger:
        return PlayerMergerImpl(dao=self)

    @property
    def level_testing_complex(self) -> LevelTestingDao:
        return LevelTestComplex(level_testing=self.level_test, game=self.game)

    @property
    def game_stat(self) -> GameStatDao:
        return GameStatImpl(dao=self)

    @property
    def typed_keys(self) -> TypedKeyGetter:
        return TypedKeyGetterImpl(dao=self)
