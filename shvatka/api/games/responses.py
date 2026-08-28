from typing import Self, overload
import typing
from dataclasses import dataclass, field
from datetime import datetime
from collections.abc import Mapping, Sequence
from uuid import UUID

from adaptix import Retort

from shvatka.api.files.responses import GameFile
from shvatka.api.shared.responses import Player, Team
from shvatka.core.games.dto import (
    BonusEvent as CoreBonusEvent,
    BonusSource,
    CurrentHintsAndKeys,
    Event,
    GameStatWithBonuses,
    MyRole,
    PassedLevelHints,
    PassedLevels,
)
from shvatka.core.models import dto, enums
from shvatka.core.models.dto import action, hints
from shvatka.core.models.enums import GameStatus


@dataclass
class Level:
    db_id: int
    name_id: str
    author: Player
    scenario: dict[str, typing.Any]
    game_id: int | None = None
    number_in_game: int | None = None

    @overload
    @classmethod
    def from_core(cls, retort: Retort, core: dto.Level) -> Self:
        ...

    @overload
    @classmethod
    def from_core(cls, retort: Retort, core: None = None) -> None:
        ...

    @classmethod
    def from_core(cls, retort: Retort, core: dto.Level | None = None) -> "Self | None":
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
class FullGame:
    id: int
    author: Player
    name: str
    status: GameStatus
    start_at: datetime | None
    levels: list[Level] = field(default_factory=list)
    files: list[GameFile] = field(default_factory=list)

    @overload
    @classmethod
    def from_core(
        cls, retort: Retort, core: dto.FullGame, files: Sequence[hints.FileMeta] = ()
    ) -> Self:
        ...

    @overload
    @classmethod
    def from_core(
        cls, retort: Retort, core: None = None, files: Sequence[hints.FileMeta] = ()
    ) -> None:
        ...

    @classmethod
    def from_core(
        cls,
        retort: Retort,
        core: dto.FullGame | None = None,
        files: Sequence[hints.FileMeta] = (),
    ) -> "Self | None":
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


@dataclass
class GameRelease:
    """A game's release: a banner leading some text, a map — as plain hints."""

    game_id: int
    banner: hints.PhotoHint | None
    """The wide title picture, shown alone above the site's header."""
    hints: Sequence[hints.AnyHint]

    @classmethod
    def from_core(cls, core: dto.GameRelease) -> "GameRelease":
        return cls(
            game_id=core.game_id,
            banner=core.banner,
            hints=core.hints,
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

    @overload
    @classmethod
    def from_core(cls, core: dto.KeyTime) -> Self:
        ...

    @overload
    @classmethod
    def from_core(cls, core: None) -> None:
        ...

    @classmethod
    def from_core(cls, core: dto.KeyTime | None) -> "Self | None":
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
    """Effects addressing ``next_level`` by number, hiding the level's name_id.

    For endpoints a playing team can read, where a name_id would leak part of
    the scenario. Resolving it needs the game's levels — see
    ``EffectsWithNameId`` for the places that don't have to hide anything.
    """

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


@dataclass(kw_only=True, frozen=True, slots=True)
class EffectsWithNameId:
    """Effects as stored, addressing ``next_level`` by the level's name_id.

    For endpoints where name_ids are not secret anyway — game results, readable
    only by orgs until the game is complete, and already carrying level name_ids
    in ``LevelTime``. Needs no level mapping, so no extra query.
    """

    id: UUID
    hints_: Sequence[hints.AnyHint]
    bonus_minutes: float
    level_up: bool
    next_level: str | None
    """name_id of the level the key routes to."""

    @classmethod
    def from_core(cls, core: action.Effects) -> "EffectsWithNameId":
        return cls(
            id=core.id,
            hints_=core.hints_,
            bonus_minutes=core.bonus_minutes,
            level_up=core.level_up,
            next_level=core.next_level,
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

    @overload
    @classmethod
    def from_core(cls, core: dto.InsertedKey, level_numbers_by_name_id: Mapping[str, int]) -> Self:
        ...

    @overload
    @classmethod
    def from_core(cls, core: None, level_numbers_by_name_id: Mapping[str, int]) -> None:
        ...

    @classmethod
    def from_core(
        cls, core: dto.InsertedKey | None, level_numbers_by_name_id: Mapping[str, int]
    ) -> "Self | None":
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

    @overload
    @classmethod
    def from_core(cls, core: dto.LevelTimeOnGame) -> Self:
        ...

    @overload
    @classmethod
    def from_core(cls, core: None) -> None:
        ...

    @classmethod
    def from_core(cls, core: dto.LevelTimeOnGame | None) -> "Self | None":
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


@dataclass(kw_only=True, frozen=True, slots=True)
class BonusEvent:
    """An event that changed a team's time, with the whole effects that caused it.

    The bonus itself is ``effects.bonus_minutes``: positive is a bonus, negative
    a penalty. Only events that carry bonus minutes are returned.
    """

    at: datetime
    effects: EffectsWithNameId
    source: BonusSource
    key: str | None
    level_time_id: int | None
    level_number: int | None
    """Level it was earned on. None when unresolved — then count it in the total only."""

    @classmethod
    def from_core(cls, core: CoreBonusEvent) -> "BonusEvent":
        return cls(
            at=core.at,
            effects=EffectsWithNameId.from_core(core.effects),
            source=core.source,
            key=core.key,
            level_time_id=core.level_time_id,
            level_number=core.level_number,
        )


@dataclass
class GameStat:
    level_times: dict[int, list[LevelTime]]
    bonuses: dict[int, list[BonusEvent]]
    """{team_id: [...]} — only teams that actually have bonuses."""

    @overload
    @classmethod
    def from_core(cls, core: GameStatWithBonuses) -> Self:
        ...

    @overload
    @classmethod
    def from_core(cls, core: None) -> None:
        ...

    @classmethod
    def from_core(cls, core: GameStatWithBonuses | None) -> "Self | None":
        if core is None:
            return None
        return cls(
            level_times={
                team.id: [LevelTime.from_core(lt) for lt in lts]
                for team, lts in core.level_times.items()
            },
            bonuses={
                team_id: [BonusEvent.from_core(bonus) for bonus in bonuses]
                for team_id, bonuses in core.bonuses.items()
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
    def from_core(cls, core: Event, level_numbers_by_name_id: Mapping[str, int]) -> Self:
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
    def from_core(cls, core: CurrentHintsAndKeys) -> Self:
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
class PassedLevel:
    level_number: int
    level_time_id: int
    started_at: datetime
    finished_at: datetime
    hints: list[hints.TimeHint]

    @classmethod
    def from_core(cls, core: PassedLevelHints) -> "PassedLevel":
        return cls(
            level_number=core.level_number,
            level_time_id=core.level_time_id,
            started_at=core.started_at,
            finished_at=core.finished_at,
            hints=core.hints,
        )


@dataclass(kw_only=True, frozen=True, slots=True)
class PassedLevelsResponse:
    game_id: int
    levels: list[PassedLevel]

    @classmethod
    def from_core(cls, core: PassedLevels) -> "PassedLevelsResponse":
        return cls(
            game_id=core.game_id,
            levels=[PassedLevel.from_core(level) for level in core.levels],
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
