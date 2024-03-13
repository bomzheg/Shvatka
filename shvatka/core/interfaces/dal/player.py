from typing import Protocol, Sequence

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.interfaces.dal.file_info import FileInfoMerger
from shvatka.core.interfaces.dal.game import ActiveGameFinder, GameAuthorMerger
from shvatka.core.interfaces.dal.key_log import PlayerKeysMerger
from shvatka.core.interfaces.dal.level import LevelAuthorMerger
from shvatka.core.interfaces.dal.organizer import PlayerOrgMerger
from shvatka.core.interfaces.dal.secure_invite import InviteRemover, InviteReader
from shvatka.core.models import dto
from shvatka.core.models import enums


class PlayerUpserter(Committer, Protocol):
    async def upsert_player(self, user: dto.User) -> dto.Player:
        raise NotImplementedError


class PlayerByIdGetter(Protocol):
    async def get_by_id(self, id_: int) -> dto.Player:
        raise NotImplementedError


class PlayerByUserIdGetter(Protocol):
    async def get_by_user_id(self, user_id: int) -> dto.Player:
        raise NotImplementedError


class PlayerByUserGetter(Protocol):
    async def get_by_user(self, user: dto.User) -> dto.Player:
        raise NotImplementedError


class TeamPlayerGetter(Protocol):
    async def get_team_player(self, player: dto.Player) -> dto.TeamPlayer:
        raise NotImplementedError


class PlayerTeamChecker(TeamPlayerGetter, Protocol):
    async def have_team(self, player: dto.Player) -> bool:
        raise NotImplementedError

    async def get_team(self, player: dto.Player) -> dto.Team | None:
        raise NotImplementedError


class PlayerPromoter(Committer, PlayerByIdGetter, InviteReader, InviteRemover, Protocol):
    async def promote(self, actor: dto.Player, target: dto.Player) -> None:
        raise NotImplementedError


class TeamJoiner(Committer, TeamPlayerGetter, Protocol):
    async def join_team(
        self, player: dto.Player, team: dto.Team, role: str, as_captain: bool = False
    ) -> None:
        raise NotImplementedError

    async def check_player_free(self, player: dto.Player) -> None:
        raise NotImplementedError


class WaiverRemover(Protocol):
    async def delete(self, waiver: dto.WaiverQuery) -> None:
        raise NotImplementedError


class PollVoteDeleter(Protocol):
    async def del_player_vote(self, team_id: int, player_id: int) -> None:
        raise NotImplementedError


class TeamLeaver(Committer, ActiveGameFinder, WaiverRemover, TeamPlayerGetter, Protocol):
    async def del_player_vote(self, team_id: int, player_id: int) -> None:
        raise NotImplementedError

    async def get_team(self, player: dto.Player) -> dto.Team | None:
        raise NotImplementedError

    async def leave_team(self, player: dto.Player) -> None:
        raise NotImplementedError


class TeamPlayersGetter(Protocol):
    async def get_players(self, team: dto.Team) -> Sequence[dto.FullTeamPlayer]:
        raise NotImplementedError


class TeamPlayerPermissionFlipper(Committer, Protocol):
    async def flip_permission(
        self, player: dto.TeamPlayer, permission: enums.TeamPlayerPermission
    ):
        raise NotImplementedError


class TeamPlayerRoleChanger(Protocol):
    async def change_role(self, team_player: dto.TeamPlayer, role: str) -> None:
        raise NotImplementedError


class TeamPlayerRoleUpdater(TeamPlayerRoleChanger, TeamPlayerGetter, Committer, Protocol):
    pass


class TeamPlayerEmojiChanger(Committer, Protocol):
    async def change_emoji(self, team_player: dto.TeamPlayer, emoji: str) -> None:
        raise NotImplementedError


class TeamPlayerEmojiUpdater(TeamPlayerEmojiChanger, TeamPlayerGetter, Committer, Protocol):
    pass


class TeamPlayerFullHistoryGetter(Protocol):
    async def get_full_history(self, player: dto.Player) -> list[dto.FullTeamPlayer]:
        raise NotImplementedError


class TeamPlayersMerger(Protocol):
    async def replace_team_players(self, primary: dto.Team, secondary: dto.Team):
        raise NotImplementedError


class TeamPlayerHistoryGetter(Protocol):
    async def get_player_teams_history(self, player: dto.Player) -> list[dto.TeamPlayer]:
        raise NotImplementedError


class TeamPlayerHistoryCleaner(Protocol):
    async def clean_history(self, player: dto.Player) -> None:
        raise NotImplementedError


class TeamPlayerHistorySetter(Protocol):
    async def set_history(self, history: list[dto.TeamPlayer]) -> None:
        raise NotImplementedError


class WaiverPlayerMerger(Protocol):
    async def replace_player_waiver(self, primary: dto.Player, secondary: dto.Player):
        raise NotImplementedError


class ForumPlayerMerger(Protocol):
    async def replace_forum_player(self, primary: dto.Player, secondary: dto.Player):
        raise NotImplementedError


class PlayerDeleter(Protocol):
    async def delete_player(self, player: dto.Player):
        raise NotImplementedError


class PlayerMerger(
    GameAuthorMerger,
    LevelAuthorMerger,
    PlayerKeysMerger,
    PlayerOrgMerger,
    TeamPlayerHistoryGetter,
    TeamPlayerHistoryCleaner,
    TeamPlayerHistorySetter,
    ForumPlayerMerger,
    PlayerDeleter,
    WaiverPlayerMerger,
    FileInfoMerger,
    Committer,
    Protocol,
):
    pass
