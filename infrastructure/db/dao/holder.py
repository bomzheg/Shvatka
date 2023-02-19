from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.interfaces.dal.game import GameUpserter, GameCreator, GamePackager
from shvatka.interfaces.dal.game_play import GamePreparer, GamePlayerDao
from shvatka.interfaces.dal.key_log import TypedKeyGetter
from shvatka.interfaces.dal.level_testing import LevelTestingDao
from shvatka.interfaces.dal.level_times import GameStarter, GameStatDao
from shvatka.interfaces.dal.organizer import OrgAdder
from shvatka.interfaces.dal.player import TeamLeaver, PlayerPromoter
from shvatka.interfaces.dal.team import TeamCreator
from shvatka.interfaces.dal.waiver import WaiverVoteAdder, WaiverVoteGetter, WaiverApprover
from .complex import WaiverVoteAdderImpl, WaiverVoteGetterImpl
from .complex.Level_times import GameStatImpl
from .complex.game import GameUpserterImpl, GameCreatorImpl, GamePackagerImpl
from .complex.game_play import GamePreparerImpl, GameStarterImpl, GamePlayerDaoImpl
from .complex.key_log import TypedKeyGetterImpl
from .complex.level_testing import LevelTestComplex
from .complex.orgs import OrgAdderImpl
from .complex.player import PlayerPromoterImpl
from .complex.team import TeamCreatorImpl, TeamLeaverImpl
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
    def __init__(self, session: AsyncSession, redis: Redis, level_test: LevelTestingData):
        self.session = session
        self.user = UserDao(self.session)
        self.chat = ChatDao(self.session)
        self.file_info = FileInfoDao(self.session)
        self.game = GameDao(self.session)
        self.level = LevelDao(self.session)
        self.level_time = LevelTimeDao(self.session)
        self.key_time = KeyTimeDao(self.session)
        self.organizer = OrganizerDao(self.session)
        self.player = PlayerDao(self.session)
        self.team_player = TeamPlayerDao(self.session)
        self.team = TeamDao(self.session)
        self.waiver = WaiverDao(self.session)
        self.achievement = AchievementDAO(self.session)
        self.forum_user = ForumUserDAO(self.session)
        self.forum_team = ForumTeamDAO(self.session)
        self.poll = PollDao(redis=redis)
        self.secure_invite = SecureInvite(redis=redis)
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
        return GamePackagerImpl(game=self.game, file_info=self.file_info)

    @property
    def team_creator(self) -> TeamCreator:
        return TeamCreatorImpl(
            team=self.team,
            team_player=self.team_player,
        )

    @property
    def team_leaver(self) -> TeamLeaver:
        return TeamLeaverImpl(
            game=self.game,
            team_player=self.team_player,
            waiver=self.waiver,
            poll=self.poll,
        )

    @property
    def game_preparer(self) -> GamePreparer:
        return GamePreparerImpl(poll=self.poll, waiver=self.waiver, org=self.organizer)

    @property
    def game_starter(self) -> GameStarter:
        return GameStarterImpl(
            game=self.game,
            waiver=self.waiver,
            level_times=self.level_time,
            level=self.level,
        )

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
        return PlayerPromoterImpl(player=self.player, secure_invite=self.secure_invite)

    @property
    def level_testing_complex(self) -> LevelTestingDao:
        return LevelTestComplex(level_testing=self.level_test, game=self.game)

    @property
    def game_stat(self) -> GameStatDao:
        return GameStatImpl(
            level_times=self.level_time, level=self.level, organizer=self.organizer
        )

    @property
    def typed_keys(self) -> TypedKeyGetter:
        return TypedKeyGetterImpl(key_time=self.key_time, organizer=self.organizer)
