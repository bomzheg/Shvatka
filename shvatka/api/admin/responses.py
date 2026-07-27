from dataclasses import dataclass

from shvatka.api.shared.responses import ForumUser, Player, Team, TgUser
from shvatka.core.models import dto, enums


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
