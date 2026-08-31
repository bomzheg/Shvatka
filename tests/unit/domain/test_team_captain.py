from datetime import UTC, datetime

from shvatka.core.models import dto

JOINED_AT = datetime(2025, 4, 12, 16, 0, tzinfo=UTC)


def _player(id_: int = 7) -> dto.Player:
    return dto.Player(id=id_, can_be_author=False, is_dummy=False, username="harry")


def _team(captain: dto.Player | None = None) -> dto.Team:
    return dto.Team(
        id=1,
        name="Gryffindor",
        captain=captain,
        is_dummy=False,
        description=None,
    )


def _team_player(team: dto.Team, player: dto.Player) -> dto.FullTeamPlayer:
    return dto.FullTeamPlayer(
        id=player.id * 10,
        player_id=player.id,
        team_id=team.id,
        date_joined=JOINED_AT,
        date_left=None,
        role="боец",
        emoji=None,
        _can_manage_waivers=False,
        _can_manage_players=False,
        _can_change_team_name=False,
        _can_add_players=False,
        _can_remove_players=False,
        player=player,
        team=team,
    )


def test_is_captain_recognises_the_captain():
    team = _team(captain=_player(7))
    assert team.is_captain(7)
    assert not team.is_captain(8)


def test_is_captain_of_a_captainless_team_is_false_for_everyone():
    """`TeamDao.create_by_forum` can leave a team without a captain."""
    assert not _team().is_captain(7)


def test_team_player_of_a_captainless_team_reads_its_permissions():
    """The regression: every permission property used to raise AttributeError here."""
    team_player = _team_player(_team(), _player(7))
    assert not team_player.is_captain
    assert not team_player.can_manage_waivers
    assert not team_player.can_manage_players
    assert not team_player.can_change_team_name
    assert not team_player.can_add_players
    assert not team_player.can_remove_players
    assert team_player.permissions


def test_the_captain_of_a_team_holds_every_permission():
    player = _player(7)
    team_player = _team_player(_team(captain=player), player)
    assert team_player.is_captain
    assert team_player.can_manage_waivers
    assert team_player.can_manage_players
    assert team_player.can_change_team_name
    assert team_player.can_add_players
    assert team_player.can_remove_players


def test_a_plain_member_holds_only_their_granted_permissions():
    team_player = _team_player(_team(captain=_player(7)), _player(8))
    assert not team_player.is_captain
    assert not team_player.can_remove_players
