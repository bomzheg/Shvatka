import typing
from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping, Sequence, Generic
from uuid import UUID

from adaptix import Retort

from shvatka.core.games.dto import CurrentHintsAndKeys, MyRole, Event
from shvatka.core.models import dto, enums
from shvatka.core.players.dto import PlayerStat as PlayerStatDto
from shvatka.core.teams.dto import TeamWithStat as TeamWithStatDto
from shvatka.core.teams.dto import TeamPlayerWithStat as TeamPlayerWithStatDto
from shvatka.core.models.dto import action
from shvatka.core.models.dto import hints
from shvatka.core.models.enums import GameStatus

T = typing.TypeVar("T")


@dataclass
class Page(Generic[T]):
    content: Sequence[T]


@dataclass
class Items(Generic[T]):
    items: Sequence[T]


@dataclass
class Player:
    id: int
    can_be_author: bool
    name_mention: str
    username: str | None

    @classmethod
    def from_core(cls, core: dto.Player):
        return cls(
            id=core.id,
            can_be_author=core.can_be_author,
            name_mention=core.name_mention,
            username=core.username,
        )


@dataclass
class Team:
    id: int
    name: str
    captain: Player | None
    description: str | None

    @classmethod
    def from_core(cls, core: dto.Team | None):
        if core is None:
            return None
        return cls(
            id=core.id,
            name=core.name,
            captain=Player.from_core(core.captain) if core.captain else None,
            description=core.description,
        )


@dataclass
class TeamWithStat:
    id: int
    name: str
    captain: Player | None
    description: str | None
    played_games_count: int

    @classmethod
    def from_core(cls, core: TeamWithStatDto) -> "TeamWithStat":
        return cls(
            id=core.team.id,
            name=core.team.name,
            captain=Player.from_core(core.team.captain) if core.team.captain else None,
            description=core.team.description,
            played_games_count=core.played_games_count,
        )


@dataclass
class TgUser:
    tg_id: int
    username: str | None
    first_name: str | None
    last_name: str | None

    @classmethod
    def from_core(cls, core: dto.User | None) -> "TgUser | None":
        if core is None:
            return None
        return cls(
            tg_id=core.tg_id,
            username=core.username,
            first_name=core.first_name,
            last_name=core.last_name,
        )


@dataclass
class ForumUser:
    name: str

    @classmethod
    def from_core(cls, core: dto.ForumUser | None) -> "ForumUser | None":
        if core is None:
            return None
        return cls(name=core.name)


@dataclass
class EmailAccount:
    email: str
    is_verified: bool

    @classmethod
    def from_core(cls, core: dto.EmailAccount | None) -> "EmailAccount | None":
        if core is None:
            return None
        return cls(email=core.email, is_verified=core.is_verified)


@dataclass
class PlayerWithIdentities:
    id: int
    can_be_author: bool
    name_mention: str
    username: str | None
    tg: TgUser | None
    forum: ForumUser | None
    email: EmailAccount | None
    is_admin: bool = False
    """whether this player may use the admin panel (tg id in configured superusers)"""

    @classmethod
    def from_core(
        cls,
        player: dto.Player,
        email: dto.EmailAccount | None,
        superusers: "Sequence[int]" = (),
    ) -> "PlayerWithIdentities":
        tg = player._user  # noqa: SLF001
        return cls(
            id=player.id,
            can_be_author=player.can_be_author,
            name_mention=player.name_mention,
            username=player.username,
            tg=TgUser.from_core(tg),
            forum=ForumUser.from_core(player._forum_user),  # noqa: SLF001
            email=EmailAccount.from_core(email),
            is_admin=tg is not None and tg.tg_id in superusers,
        )


@dataclass
class AdminPlayer:
    id: int
    can_be_author: bool
    name_mention: str
    username: str | None
    tg: TgUser | None
    forum: ForumUser | None

    @classmethod
    def from_core(cls, core: dto.Player) -> "AdminPlayer":
        return cls(
            id=core.id,
            can_be_author=core.can_be_author,
            name_mention=core.name_mention,
            username=core.username,
            tg=TgUser.from_core(core._user),  # noqa: SLF001
            forum=ForumUser.from_core(core._forum_user),  # noqa: SLF001
        )


@dataclass
class OneTimeLink:
    url: str


@dataclass(kw_only=True, frozen=True, slots=True)
class PollEntry:
    player: Player
    vote: enums.Played

    @classmethod
    def from_core(cls, vote: enums.Played, voted: dto.VotedPlayer) -> "PollEntry":
        return cls(player=Player.from_core(voted.player), vote=vote)


@dataclass(kw_only=True, frozen=True, slots=True)
class AdminPollTeam:
    team: Team | None
    entries: list[PollEntry]

    @classmethod
    def from_core(
        cls, team: dto.Team, votes: dict[enums.Played, list[dto.VotedPlayer]]
    ) -> "AdminPollTeam":
        return cls(
            team=Team.from_core(team),
            entries=[
                PollEntry.from_core(vote, voted)
                for vote, voted_players in votes.items()
                for voted in voted_players
            ],
        )


@dataclass
class AdminPoll:
    teams: list[AdminPollTeam]

    @classmethod
    def from_core(
        cls, poll: "dict[dto.Team, dict[enums.Played, list[dto.VotedPlayer]]]"
    ) -> "AdminPoll":
        return cls(teams=[AdminPollTeam.from_core(team, votes) for team, votes in poll.items()])


@dataclass
class TeamPlayer:
    id: int
    team: Team | None
    date_joined: datetime
    role: str
    emoji: str | None

    @classmethod
    def from_core(cls, core: dto.FullTeamPlayer | None) -> "TeamPlayer | None":
        if core is None:
            return None
        return cls(
            id=core.id,
            team=Team.from_core(core.team),
            date_joined=core.date_joined,
            role=core.role,
            emoji=core.emoji,
        )


@dataclass
class TeamPlayerHistory:
    team_player_id: int
    team: Team | None
    date_joined: datetime
    date_left: datetime | None
    role: str
    emoji: str | None

    @classmethod
    def from_core(cls, core: dto.FullTeamPlayer) -> "TeamPlayerHistory":
        return cls(
            team_player_id=core.id,
            team=Team.from_core(core.team),
            date_joined=core.date_joined,
            date_left=core.date_left,
            role=core.role,
            emoji=core.emoji,
        )


@dataclass
class PlayerStat:
    id: int
    username: str | None
    can_be_author: bool
    typed_keys_count: int
    typed_correct_keys_count: int
    team_history: list[TeamPlayerHistory]
    played_games: list["Game"]

    @classmethod
    def from_core(cls, core: PlayerStatDto) -> "PlayerStat":
        return cls(
            id=core.player.id,
            username=core.player.username,
            can_be_author=core.player.can_be_author,
            typed_keys_count=core.player.typed_keys_count,
            typed_correct_keys_count=core.player.typed_correct_keys_count,
            team_history=[TeamPlayerHistory.from_core(tp) for tp in core.team_history],
            played_games=[Game.from_core(game) for game in core.played_games],
        )


@dataclass
class FullPlayer:
    id: int
    username: str | None
    can_be_author: bool
    tg: TgUser | None
    player_in_team: TeamPlayer | None

    @classmethod
    def from_core(cls, player: dto.Player, team_player: dto.FullTeamPlayer | None) -> "FullPlayer":
        return cls(
            id=player.id,
            username=player.username,
            can_be_author=player.can_be_author,
            tg=TgUser.from_core(player._user),  # noqa: SLF001
            player_in_team=TeamPlayer.from_core(team_player),
        )


@dataclass
class TeamMember:
    team_player_id: int
    id: int
    username: str | None
    can_be_author: bool
    emoji: str | None
    role: str
    permissions: dict[str, bool]
    date_joined: datetime

    @classmethod
    def from_core(cls, core: dto.FullTeamPlayer) -> "TeamMember":
        return cls(
            team_player_id=core.id,
            id=core.player.id,
            username=core.player.username,
            can_be_author=core.player.can_be_author,
            emoji=core.emoji,
            role=core.role,
            permissions={permission.name: value for permission, value in core.permissions.items()},
            date_joined=core.date_joined,
        )


@dataclass
class TeamMemberWithStat:
    team_player_id: int
    id: int
    username: str | None
    can_be_author: bool
    emoji: str | None
    role: str
    permissions: dict[str, bool]
    date_joined: datetime
    played_games_count: int

    @classmethod
    def from_core(cls, core: TeamPlayerWithStatDto) -> "TeamMemberWithStat":
        tp = core.team_player
        return cls(
            team_player_id=tp.id,
            id=tp.player.id,
            username=tp.player.username,
            can_be_author=tp.player.can_be_author,
            emoji=tp.emoji,
            role=tp.role,
            permissions={permission.name: value for permission, value in tp.permissions.items()},
            date_joined=tp.date_joined,
            played_games_count=core.played_games_count,
        )


@dataclass
class Game:
    id: int
    author: Player
    name: str
    status: GameStatus
    start_at: datetime | None = None
    number: int | None = None

    @classmethod
    def from_core(cls, core: dto.Game | None):
        if core is None:
            return None
        return cls(
            id=core.id,
            author=Player.from_core(core.author),
            name=core.name,
            status=core.status,
            start_at=core.start_at,
            number=core.number,
        )


@dataclass
class Level:
    db_id: int
    name_id: str
    author: Player
    scenario: dict[str, typing.Any]
    game_id: int | None = None
    number_in_game: int | None = None

    @classmethod
    def from_core(cls, retort: Retort, core: dto.Level | None = None):
        if core is None:
            return None
        return cls(
            db_id=core.db_id,
            name_id=core.name_id,
            author=Player.from_core(core.author),
            scenario=retort.dump(core.scenario),
            game_id=core.game_id,
            number_in_game=core.number_in_game,
        )


@dataclass
class GameFile:
    guid: str
    original_filename: str
    extension: str
    content_type: enums.HintType | None
    mime_type: str | None

    @classmethod
    def from_core(cls, core: hints.FileMeta) -> "GameFile":
        return cls(
            guid=core.guid,
            original_filename=core.original_filename,
            extension=core.extension,
            content_type=core.content_type,
            mime_type=core.mime_type,
        )


@dataclass
class FullGame:
    id: int
    author: Player
    name: str
    status: GameStatus
    start_at: datetime | None
    levels: list[Level] = field(default_factory=list)
    files: list[GameFile] = field(default_factory=list)

    @classmethod
    def from_core(
        cls,
        retort: Retort,
        core: dto.FullGame | None = None,
        files: Sequence[hints.FileMeta] = (),
    ):
        if core is None:
            return None
        return cls(
            id=core.id,
            author=Player.from_core(core.author),
            name=core.name,
            status=core.status,
            start_at=core.start_at,
            levels=[Level.from_core(retort, level) for level in core.levels],
            files=[GameFile.from_core(file) for file in files],
        )


@dataclass(frozen=True)
class KeyTime:
    text: str
    type_: enums.KeyType
    is_duplicate: bool
    at: datetime
    level_number: int
    player: Player
    team: Team

    @classmethod
    def from_core(cls, core: dto.KeyTime | None):
        if core is None:
            return None
        return cls(
            text=core.text,
            type_=core.type_,
            is_duplicate=core.is_duplicate,
            at=core.at,
            level_number=core.level_number,
            player=Player.from_core(core.player),
            team=Team.from_core(core.team),
        )


@dataclass(kw_only=True, frozen=True, slots=True)
class Effects:
    id: UUID
    hints_: Sequence[hints.AnyHint]
    bonus_minutes: float
    level_up: bool
    next_level: int | None
    """number_in_game of the level the key routes to (resolved from name_id)."""

    @classmethod
    def from_core(
        cls, core: action.Effects, level_numbers_by_name_id: Mapping[str, int]
    ) -> "Effects":
        return cls(
            id=core.id,
            hints_=core.hints_,
            bonus_minutes=core.bonus_minutes,
            level_up=core.level_up,
            next_level=(
                level_numbers_by_name_id.get(core.next_level)
                if core.next_level is not None
                else None
            ),
        )


@dataclass(frozen=True)
class KeyWithEffects:
    text: str
    type_: enums.KeyType
    is_duplicate: bool
    at: datetime
    level_number: int
    player: Player
    team: Team
    effects: Effects | None

    @classmethod
    def from_core(cls, core: dto.InsertedKey | None, level_numbers_by_name_id: Mapping[str, int]):
        if core is None:
            return None
        return cls(
            text=core.text,
            type_=core.type_,
            is_duplicate=core.is_duplicate,
            at=core.at,
            level_number=core.level_number,
            player=Player.from_core(core.player),
            team=Team.from_core(core.team),
            effects=(
                Effects.from_core(core.parsed_key.effect, level_numbers_by_name_id)
                if core.parsed_key is not None
                else None
            ),
        )


@dataclass
class LevelTime:
    id: int
    team: Team
    level_number: int
    name_id: str | None
    start_at: datetime
    is_finished: bool

    @classmethod
    def from_core(cls, core: dto.LevelTimeOnGame | None):
        if core is None:
            return None
        return cls(
            id=core.id,
            team=Team.from_core(core.team),
            level_number=core.level_number,
            name_id=core.name_id,
            start_at=core.start_at,
            is_finished=core.is_finished,
        )


@dataclass
class GameStat:
    level_times: dict[int, list[LevelTime]]

    @classmethod
    def from_core(cls, core: dto.GameStatWithHints | None):
        if core is None:
            return None
        return cls(
            level_times={
                team.id: [LevelTime.from_core(lt) for lt in lts]
                for team, lts in core.level_times.items()
            },
        )


@dataclass(kw_only=True, frozen=True, slots=True)
class GameEvent:
    id: int
    level_time_id: int
    at: datetime
    effects: Effects
    key: str | None = None
    is_timer: bool = False

    @classmethod
    def from_core(cls, core: Event, level_numbers_by_name_id: Mapping[str, int]):
        return cls(
            id=core.id,
            level_time_id=core.level_time_id,
            at=core.at,
            effects=Effects.from_core(core.effects, level_numbers_by_name_id),
            key=core.key,
            is_timer=core.is_timer,
        )


@dataclass(kw_only=True, frozen=True, slots=True)
class CurrentHintResponse:
    hints: list[hints.TimeHint]
    typed_keys: list[KeyWithEffects]
    events: list[GameEvent]
    game_id: int
    level_number: int
    level_time_id: int
    started_at: datetime
    is_finished: bool

    @classmethod
    def from_core(cls, core: CurrentHintsAndKeys):
        if core is None:
            return None
        level_numbers_by_name_id = core.level_numbers_by_name_id
        return cls(
            game_id=core.game_id,
            hints=core.hints,
            typed_keys=[
                KeyWithEffects.from_core(kt, level_numbers_by_name_id) for kt in core.typed_keys
            ],
            events=[GameEvent.from_core(e, level_numbers_by_name_id) for e in core.events],
            level_number=core.level_number,
            started_at=core.started_at,
            level_time_id=core.level_time_id,
            is_finished=core.is_finished,
        )


@dataclass(kw_only=True, frozen=True, slots=True)
class InsertedKey:
    text: str
    is_duplicate: bool
    wrong: bool
    at: datetime | None
    effects: list[Effects]
    game_finished: bool


@dataclass(kw_only=True)
class OrganizerDto:
    player: Player
    can_spy: bool
    can_see_log_keys: bool
    can_validate_waivers: bool
    view_scenario: bool
    deleted: bool

    @classmethod
    def from_core(cls, core: dto.Organizer | None) -> "OrganizerDto | None":
        if core is None:
            return None
        return cls(
            player=Player.from_core(core.player),
            can_spy=core.can_spy,
            can_see_log_keys=core.can_see_log_keys,
            can_validate_waivers=core.can_validate_waivers,
            view_scenario=core.view_scenario,
            deleted=core.deleted,
        )


@dataclass(kw_only=True)
class GameOrganizer:
    org_id: int | None
    player: Player
    can_spy: bool
    can_see_log_keys: bool
    can_validate_waivers: bool
    view_scenario: bool
    deleted: bool

    @classmethod
    def from_core(cls, core: dto.Organizer) -> "GameOrganizer":
        return cls(
            org_id=getattr(core, "id", None),
            player=Player.from_core(core.player),
            can_spy=core.can_spy,
            can_see_log_keys=core.can_see_log_keys,
            can_validate_waivers=core.can_validate_waivers,
            view_scenario=core.view_scenario,
            deleted=core.deleted,
        )


@dataclass(kw_only=True)
class MyRoleDto:
    waiver_vote: enums.Played | None
    team: Team | None
    org: OrganizerDto | None

    @classmethod
    def from_core(cls, core: MyRole) -> "MyRoleDto":
        return cls(
            waiver_vote=core.waiver_vote,
            team=Team.from_core(core.team),
            org=OrganizerDto.from_core(core.org),
        )


@dataclass(frozen=True, slots=True)
class PushConfigResponse:
    enabled: bool
    public_key: str | None


@dataclass
class UploadedFile:
    guid: str
    original_filename: str
    extension: str
    content_type: enums.HintType | None
    mime_type: str | None

    @classmethod
    def from_core(cls, core: hints.SavedFileMeta) -> "UploadedFile":
        return cls(
            guid=core.guid,
            original_filename=core.original_filename,
            extension=core.extension,
            content_type=core.content_type,
            mime_type=core.mime_type,
        )


@dataclass(kw_only=True, frozen=True, slots=True)
class WaiverPlayer:
    player: Player
    played: enums.Played

    @classmethod
    def from_core(cls, waiver: dto.Waiver) -> "WaiverPlayer":
        return cls(player=Player.from_core(waiver.player), played=waiver.played)


@dataclass(kw_only=True, frozen=True, slots=True)
class TeamWaivers:
    team: Team | None
    players: list[WaiverPlayer]

    @classmethod
    def from_core(cls, team: dto.Team, waivers: list[dto.Waiver]) -> "TeamWaivers":
        return cls(
            team=Team.from_core(team),
            players=[WaiverPlayer.from_core(w) for w in waivers],
        )
