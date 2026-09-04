from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from shvatka.api.shared.responses import Game, Player, Team
from shvatka.core.models import dto, enums
from shvatka.core.players.dto import WaiverPoint as WaiverPointDto


@dataclass
class VotedPlayer:
    player: Player

    @classmethod
    def from_core(cls, voted: dto.VotedPlayer) -> "VotedPlayer":
        return cls(player=Player.from_core(voted.player))


@dataclass(kw_only=True, frozen=True, slots=True)
class WaiversDto:
    teams: list[Team]
    waivers: dict[int, list[VotedPlayer]]

    @classmethod
    def from_core(cls, waiver: dict[dto.Team, Iterable[dto.VotedPlayer]]) -> "WaiversDto":
        return cls(
            teams=[Team.from_core(team) for team in waiver],
            waivers={
                team.id: [VotedPlayer.from_core(w) for w in waivers]
                for team, waivers in waiver.items()
            },
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


@dataclass(kw_only=True, frozen=True, slots=True)
class WaiverPoint:
    game: Game
    team: Team | None
    at_since: datetime
    at_until: datetime

    @classmethod
    def from_core(cls, core: WaiverPointDto) -> "WaiverPoint":
        return cls(
            game=Game.from_core(core.game),
            team=Team.from_core(core.team),
            at_since=core.at_since,
            at_until=core.at_until,
        )
