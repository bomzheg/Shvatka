from datetime import date

import pytest

from shvatka.core.season import dto as season_dto
from shvatka.core.season.rules import check_can_edit_slot, check_can_take_slot
from shvatka.core.utils import exceptions
from tests.unit.season.conftest import make_player, make_slot, make_team

DAY = date(2027, 5, 15)


def test_a_free_date_may_be_taken_by_any_author():
    check_can_take_slot(
        make_slot(1, DAY),
        make_player(1),
        author_kind=season_dto.SlotAuthorKind.player,
        team=None,
    )


def test_a_player_without_promotion_may_not_take_a_date():
    with pytest.raises(exceptions.CantBeAuthor):
        check_can_take_slot(
            make_slot(1, DAY),
            make_player(1, can_be_author=False),
            author_kind=season_dto.SlotAuthorKind.player,
            team=None,
        )


def test_someone_elses_date_may_not_be_taken():
    owner = make_player(1)
    with pytest.raises(exceptions.SlotAlreadyTaken):
        check_can_take_slot(
            make_slot(1, DAY, owner=owner),
            make_player(2),
            author_kind=season_dto.SlotAuthorKind.player,
            team=None,
        )


def test_re_taking_your_own_date_is_how_the_author_is_changed():
    owner = make_player(1)
    check_can_take_slot(
        make_slot(1, DAY, owner=owner),
        owner,
        author_kind=season_dto.SlotAuthorKind.player,
        team=None,
    )


def test_a_superuser_takes_a_date_belonging_to_someone_else():
    check_can_take_slot(
        make_slot(1, DAY, owner=make_player(1)),
        make_player(2),
        author_kind=season_dto.SlotAuthorKind.player,
        team=None,
        is_superuser=True,
    )


def test_only_the_captain_signs_their_team_up():
    captain = make_player(1)
    teammate = make_player(2)
    team = make_team(10, captain)

    check_can_take_slot(
        make_slot(1, DAY),
        captain,
        author_kind=season_dto.SlotAuthorKind.team,
        team=team,
    )
    with pytest.raises(exceptions.SlotAuthorInvalid):
        check_can_take_slot(
            make_slot(1, DAY),
            teammate,
            author_kind=season_dto.SlotAuthorKind.team,
            team=team,
        )


def test_a_team_author_needs_a_team():
    with pytest.raises(exceptions.SlotAuthorInvalid):
        check_can_take_slot(
            make_slot(1, DAY),
            make_player(1),
            author_kind=season_dto.SlotAuthorKind.team,
            team=None,
        )


def test_a_free_date_may_be_edited_by_any_author():
    check_can_edit_slot(make_slot(1, DAY), make_player(2))


def test_a_taken_date_may_be_edited_only_by_its_owner():
    owner = make_player(1)
    slot = make_slot(1, DAY, owner=owner)

    check_can_edit_slot(slot, owner)
    check_can_edit_slot(slot, make_player(2), is_superuser=True)
    with pytest.raises(exceptions.NotSlotOwner):
        check_can_edit_slot(slot, make_player(2))
