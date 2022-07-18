from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.dao import (
    ChatDao, UserDao, FileInfoDao, GameDao, LevelDao,
    LevelTimeDao, KeyTimeDao, OrganizerDao, PlayerDao,
    PlayerInTeamDao, TeamDao, WaiverDao,
)


@dataclass
class HolderDao:
    session: AsyncSession
    user: UserDao = field(init=False)
    chat: ChatDao = field(init=False)
    file_info: FileInfoDao = field(init=False)
    game: GameDao = field(init=False)
    level: LevelDao = field(init=False)
    level_time: LevelTimeDao = field(init=False)
    key_time: KeyTimeDao = field(init=False)
    organizer: OrganizerDao = field(init=False)
    player: PlayerDao = field(init=False)
    player_in_team: PlayerInTeamDao = field(init=False)
    team: TeamDao = field(init=False)
    waiver: WaiverDao = field(init=False)

    def __post_init__(self):
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

    async def commit(self):
        await self.session.commit()
