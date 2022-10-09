from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.dal.game import GameUpserter
from shvatka.dal.game_play import GamePreparer, KeyChecker
from shvatka.dal.level_times import GameStarter
from shvatka.dal.player import TeamLeaver
from shvatka.dal.team import TeamCreator
from shvatka.dal.waiver import WaiverVoteAdder, WaiverVoteGetter, WaiverApprover
from .complex import WaiverVoteAdderImpl, WaiverVoteGetterImpl
from .complex.game import GameUpserterImpl
from .complex.game_play import GamePreparerImpl, GameStarterImpl, KeyCheckerImpl
from .complex.team import TeamCreatorImpl, TeamLeaverImpl
from .complex.waiver import WaiverApproverImpl
from .rdb import (
    ChatDao, UserDao, FileInfoDao, GameDao, LevelDao,
    LevelTimeDao, KeyTimeDao, OrganizerDao, PlayerDao,
    PlayerInTeamDao, TeamDao, WaiverDao,
)
from .redis import PollDao


class HolderDao:
    def __init__(self, session: AsyncSession, redis: Redis):
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
        self.player_in_team = PlayerInTeamDao(self.session)
        self.team = TeamDao(self.session)
        self.waiver = WaiverDao(self.session)
        self.poll = PollDao(redis)

    async def commit(self):
        await self.session.commit()

    @property
    def waiver_vote_adder(self) -> WaiverVoteAdder:
        return WaiverVoteAdderImpl(poll=self.poll, waiver=self.waiver)

    @property
    def waiver_vote_getter(self) -> WaiverVoteGetter:
        return WaiverVoteGetterImpl(poll=self.poll, player=self.player)

    @property
    def waiver_approver(self) -> WaiverApprover:
        return WaiverApproverImpl(
            poll=self.poll, player=self.player, waiver=self.waiver,
        )

    @property
    def game_upserter(self) -> GameUpserter:
        return GameUpserterImpl(game=self.game, level=self.level)

    @property
    def team_creator(self) -> TeamCreator:
        return TeamCreatorImpl(
            team=self.team, player_in_team=self.player_in_team,
        )

    @property
    def team_leaver(self) -> TeamLeaver:
        return TeamLeaverImpl(
            game=self.game, player_in_team=self.player_in_team,
            waiver=self.waiver, poll=self.poll,
        )

    @property
    def game_preparer(self) -> GamePreparer:
        return GamePreparerImpl(poll=self.poll, waiver=self.waiver, org=self.organizer)

    @property
    def game_starter(self) -> GameStarter:
        return GameStarterImpl(game=self.game, waiver=self.waiver, level_times=self.level_time, level=self.level)

    @property
    def key_checker(self) -> KeyChecker:
        return KeyCheckerImpl(level_time=self.level_time, level=self.level, key_time=self.key_time)
