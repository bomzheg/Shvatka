from datetime import UTC, datetime

import pytest

from shvatka.core.models import dto
from shvatka.core.services.team import change_captain, check_can_change_captain
from shvatka.core.utils.defaults_constants import CAPTAIN_ROLE, DEFAULT_ROLE
from shvatka.core.utils.exceptions import PermissionsError, PlayerNotInTeam, TeamError
from shvatka.core.views.team import CaptainChanged, TeamEvent

JOINED_AT = datetime(2025, 4, 12, 16, 0, tzinfo=UTC)


def _player(id_: int, username: str) -> dto.Player:
    return dto.Player(id=id_, can_be_author=False, is_dummy=False, username=username)


def _team(captain: dto.Player | None) -> dto.Team:
    return dto.Team(
        id=1,
        name="Gryffindor",
        captain=captain,
        is_dummy=False,
        description=None,
        chat=None,
    )


def _team_player(player: dto.Player, team: dto.Team, role: str) -> dto.FullTeamPlayer:
    return dto.FullTeamPlayer(
        id=player.id * 10,
        player_id=player.id,
        team_id=team.id,
        date_joined=JOINED_AT,
        date_left=None,
        role=role,
        emoji=None,
        _can_manage_waivers=False,
        _can_manage_players=False,
        _can_change_team_name=False,
        _can_add_players=False,
        _can_remove_players=False,
        player=player,
        team=team,
    )


class FakeCaptainSetterDao:
    def __init__(self, team: dto.Team, players: list[dto.FullTeamPlayer]) -> None:
        self.team = team
        self.players = players
        self.roles: list[tuple[int, str]] = []
        self.new_captain: dto.Player | None = None
        self.commits = 0

    async def get_by_id(self, id_: int) -> dto.Team:
        return self.team

    async def get_players(self, team: dto.Team) -> list[dto.FullTeamPlayer]:
        return self.players

    async def change_captain(self, team: dto.Team, captain: dto.Player) -> None:
        self.new_captain = captain
        self.team = _team(captain)

    async def change_role(self, team_player: dto.TeamPlayer, role: str) -> None:
        self.roles.append((team_player.player_id, role))

    async def commit(self) -> None:
        self.commits += 1


class FakeNotifier:
    def __init__(self) -> None:
        self.events: list[TeamEvent] = []

    async def notify(self, event: TeamEvent) -> None:
        self.events.append(event)


@pytest.mark.asyncio
async def test_change_captain_swaps_roles() -> None:
    harry, ron = _player(1, "harry"), _player(2, "ron")
    team = _team(harry)
    dao = FakeCaptainSetterDao(
        team,
        [_team_player(harry, team, CAPTAIN_ROLE), _team_player(ron, team, DEFAULT_ROLE)],
    )
    notifier = FakeNotifier()

    updated = await change_captain(team, harry, ron.id, dao, notifier)

    assert dao.new_captain == ron
    assert updated.captain == ron
    assert dao.roles == [(ron.id, CAPTAIN_ROLE), (harry.id, DEFAULT_ROLE)]
    assert dao.commits == 1
    (event,) = notifier.events
    assert isinstance(event, CaptainChanged)
    assert event.new_captain == ron
    assert event.old_captain == harry
    assert event.by_old_captain


@pytest.mark.asyncio
async def test_change_captain_keeps_a_custom_role_of_the_old_captain() -> None:
    harry, ron = _player(1, "harry"), _player(2, "ron")
    team = _team(harry)
    dao = FakeCaptainSetterDao(
        team,
        [_team_player(harry, team, "водитель"), _team_player(ron, team, DEFAULT_ROLE)],
    )

    await change_captain(team, harry, ron.id, dao, FakeNotifier())

    assert dao.roles == [(ron.id, CAPTAIN_ROLE)]


@pytest.mark.asyncio
async def test_change_captain_when_the_old_one_already_left() -> None:
    harry, ron = _player(1, "harry"), _player(2, "ron")
    team = _team(harry)
    dao = FakeCaptainSetterDao(team, [_team_player(ron, team, DEFAULT_ROLE)])
    notifier = FakeNotifier()

    await change_captain(team, harry, ron.id, dao, notifier)

    assert dao.roles == [(ron.id, CAPTAIN_ROLE)]
    assert notifier.events[0].old_captain == harry  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_change_captain_to_a_player_outside_the_team() -> None:
    harry, draco = _player(1, "harry"), _player(3, "draco")
    team = _team(harry)
    dao = FakeCaptainSetterDao(team, [_team_player(harry, team, CAPTAIN_ROLE)])
    notifier = FakeNotifier()

    with pytest.raises(PlayerNotInTeam):
        await change_captain(team, harry, draco.id, dao, notifier)

    assert dao.new_captain is None
    assert dao.commits == 0
    assert notifier.events == []


@pytest.mark.asyncio
async def test_change_captain_to_the_current_captain() -> None:
    harry = _player(1, "harry")
    team = _team(harry)
    dao = FakeCaptainSetterDao(team, [_team_player(harry, team, CAPTAIN_ROLE)])

    with pytest.raises(TeamError):
        await change_captain(team, harry, harry.id, dao, FakeNotifier())

    assert dao.commits == 0


def test_only_the_captain_may_hand_the_team_over() -> None:
    harry, ron = _player(1, "harry"), _player(2, "ron")
    team = _team(harry)

    check_can_change_captain(harry, team)

    with pytest.raises(PermissionsError):
        check_can_change_captain(ron, team)


def test_a_team_without_a_captain_has_nobody_to_hand_it_over() -> None:
    with pytest.raises(PermissionsError):
        check_can_change_captain(_player(1, "harry"), _team(None))
