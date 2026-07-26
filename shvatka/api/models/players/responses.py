from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from shvatka.api.models.shared.responses import (
    EmailAccount,
    ForumUser,
    Game,
    Team,
    TgUser,
)
from shvatka.core.models import dto
from shvatka.core.players.dto import PlayerStat as PlayerStatDto


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
    played_games: list[Game]

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
