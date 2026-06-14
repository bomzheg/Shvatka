import typing
from dataclasses import dataclass, field
from datetime import datetime
from typing import Sequence, Generic

from adaptix import Retort

from shvatka.core.games.dto import CurrentHintsAndKeys, MyRole, Event
from shvatka.core.models import dto, enums
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

    @classmethod
    def from_core(cls, core: dto.Player):
        return cls(
            id=core.id,
            can_be_author=core.can_be_author,
            name_mention=core.name_mention,
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

    @classmethod
    def from_core(cls, core: hints.FileMeta) -> "GameFile":
        return cls(
            guid=core.guid,
            original_filename=core.original_filename,
            extension=core.extension,
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


@dataclass(frozen=True)
class KeyWithEffects:
    text: str
    type_: enums.KeyType
    is_duplicate: bool
    at: datetime
    level_number: int
    player: Player
    team: Team
    effects: action.Effects

    @classmethod
    def from_core(cls, core: dto.InsertedKey | None):
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
            effects=core.parsed_key.effect if core.parsed_key is not None else None,
        )


@dataclass
class LevelTime:
    id: int
    team: Team
    level_number: int
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
    effects: action.Effects
    key: str | None = None
    is_timer: bool = False

    @classmethod
    def from_core(cls, core: Event):
        return cls(
            id=core.id,
            level_time_id=core.level_time_id,
            at=core.at,
            effects=core.effects,
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

    @classmethod
    def from_core(cls, core: CurrentHintsAndKeys):
        if core is None:
            return None
        return cls(
            game_id=core.game_id,
            hints=core.hints,
            typed_keys=[KeyWithEffects.from_core(kt) for kt in core.typed_keys],
            events=[GameEvent.from_core(e) for e in core.events],
            level_number=core.level_number,
            started_at=core.started_at,
            level_time_id=core.level_time_id,
        )


@dataclass(kw_only=True, frozen=True, slots=True)
class InsertedKey:
    text: str
    is_duplicate: bool
    wrong: bool
    at: datetime | None
    effects: list[action.Effects]
    game_finished: bool


@dataclass(kw_only=True)
class OrganizerDto:
    player: Player
    can_spy: bool
    can_see_log_keys: bool
    can_validate_waivers: bool
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
