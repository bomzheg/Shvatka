from datetime import date

import pytest

from shvatka.core.season import dto as season_dto
from shvatka.core.season.rules import check_can_edit_schedule, check_can_take_slot
from shvatka.core.utils import exceptions
from tests.unit.season.conftest import make_player, make_slot, make_team

DAY = date(2027, 5, 15)


def test_promotion_is_the_whole_gate():
    check_can_edit_schedule(make_player(1))

    with pytest.raises(exceptions.CantBeAuthor):
        check_can_edit_schedule(make_player(2, can_be_author=False))


def test_any_author_may_edit_any_date_including_someone_elses():
    # ownership records who intends to make the game, not who may touch the
    # row — so a claimed date needs no admin to unstick it
    slot = make_slot(1, DAY, owner=make_player(1))

    check_can_edit_schedule(make_player(2))
    assert slot.owner is not None


def test_a_free_date_may_be_taken_by_any_author():
    check_can_take_slot(make_player(1), author_kind=season_dto.SlotAuthorKind.player, team=None)


def test_a_player_without_promotion_may_not_take_a_date():
    with pytest.raises(exceptions.CantBeAuthor):
        check_can_take_slot(
            make_player(1, can_be_author=False),
            author_kind=season_dto.SlotAuthorKind.player,
            team=None,
        )


def test_only_the_captain_signs_their_team_up():
    captain = make_player(1)
    teammate = make_player(2)
    team = make_team(10, captain)

    check_can_take_slot(captain, author_kind=season_dto.SlotAuthorKind.team, team=team)
    with pytest.raises(exceptions.SlotAuthorInvalid):
        check_can_take_slot(teammate, author_kind=season_dto.SlotAuthorKind.team, team=team)


def test_a_team_author_needs_a_team():
    with pytest.raises(exceptions.SlotAuthorInvalid):
        check_can_take_slot(make_player(1), author_kind=season_dto.SlotAuthorKind.team, team=None)
