"""``check_is_org`` — the org lookup read as the permission check it is."""

import pytest

from shvatka.core.models import dto
from shvatka.core.models.dto import GameResults
from shvatka.core.models.enums import GameStatus
from shvatka.core.services.organizers import check_is_org
from shvatka.core.utils import exceptions


def make_player(id_: int) -> dto.Player:
    return dto.Player(id=id_, can_be_author=True, is_dummy=False, username=f"player{id_}")


def make_game(id_: int, author: dto.Player) -> dto.Game:
    return dto.Game(
        id=id_,
        author=author,
        name=f"game{id_}",
        status=GameStatus.started,
        manage_token="token",
        start_at=None,
        number=None,
        results=GameResults(published_chanel_id=None, results_picture_file_id=None, keys_url=None),
    )


def make_org(player: dto.Player, game: dto.Game) -> dto.SecondaryOrganizer:
    return dto.SecondaryOrganizer(
        id=1,
        player=player,
        game=game,
        can_spy=True,
        can_see_log_keys=True,
        can_validate_waivers=True,
        view_scenario=True,
        deleted=False,
    )


def test_an_org_of_this_game_passes_through():
    author = make_player(1)
    game = make_game(10, author)
    player = make_player(2)
    org = make_org(player, game)

    assert check_is_org(org, player, game) is org


def test_not_an_org_is_refused():
    author = make_player(1)
    game = make_game(10, author)

    with pytest.raises(exceptions.NotAuthorizedForEdit):
        check_is_org(None, make_player(2), game)


def test_another_players_org_is_refused():
    """The row that came back has to be the acting player's, not just any."""
    author = make_player(1)
    game = make_game(10, author)
    org = make_org(make_player(3), game)

    with pytest.raises(exceptions.NotAuthorizedForEdit):
        check_is_org(org, make_player(2), game)


def test_an_org_of_another_game_is_refused():
    """Being an org somewhere is not being an org here."""
    author = make_player(1)
    player = make_player(2)
    org = make_org(player, make_game(11, author))

    with pytest.raises(exceptions.NotAuthorizedForEdit):
        check_is_org(org, player, make_game(10, author))
