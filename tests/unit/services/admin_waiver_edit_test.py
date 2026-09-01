"""Adding and removing one waiver from the admin panel.

The captain is gone, or missed the deadline, and a team's roster is wrong on
the evening of the game. These pin down the two ways the panel puts it right —
and the one thing it refuses: signing up somebody who does not play in the team.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime

import pytest

from shvatka.core.models import dto
from shvatka.core.models.dto import GameResults
from shvatka.core.models.enums import GameStatus, Played
from shvatka.core.utils import exceptions
from shvatka.core.utils.defaults_constants import DEFAULT_ROLE
from shvatka.core.waiver.admin_interactors import (
    AdminAddWaiverInteractor,
    AdminRemoveWaiverInteractor,
)
from tests.fixtures.identity import MockIdentityProvider


def make_player(id_: int) -> dto.Player:
    return dto.Player(id=id_, can_be_author=True, is_dummy=False, username=f"player{id_}")


def make_team(id_: int) -> dto.Team:
    return dto.Team(
        id=id_,
        name=f"team{id_}",
        captain=make_player(1),
        description=None,
        is_dummy=False,
    )


def make_game(id_: int = 10) -> dto.Game:
    return dto.Game(
        id=id_,
        author=make_player(1),
        name="my game",
        status=GameStatus.getting_waivers,
        manage_token="token",
        start_at=None,
        number=None,
        results=GameResults(published_chanel_id=None, results_picture_file_id=None, keys_url=None),
    )


@dataclass
class FakeWaiverDao:
    """In-memory stand-in for ``AdminWaiverEditor``."""

    game: dto.Game
    team: dto.Team
    players: dict[int, dto.Player] = field(default_factory=dict)
    """every player the panel may name"""
    team_of: dict[int, int] = field(default_factory=dict)
    """player id -> the team they currently play in"""
    waivers: list[dto.Waiver] = field(default_factory=list)
    committed: int = 0

    async def get_game_by_id(self, id_: int) -> dto.Game:
        if id_ != self.game.id:
            raise exceptions.GameNotFound(game_id=id_)
        return self.game

    async def get_team_by_id(self, id_: int) -> dto.Team:
        if id_ != self.team.id:
            raise exceptions.TeamError(team_id=id_)
        return self.team

    async def get_player_by_id(self, id_: int) -> dto.Player:
        try:
            return self.players[id_]
        except KeyError as e:
            raise exceptions.PlayerNotFoundError(player_id=id_) from e

    async def get_team_player(self, player: dto.Player) -> dto.TeamPlayer:
        return dto.TeamPlayer(
            id=player.id,
            player_id=player.id,
            team_id=self.team_of.get(player.id, 0),
            date_joined=datetime(2025, 4, 1, tzinfo=UTC),
            date_left=None,
            role=DEFAULT_ROLE,
            emoji=None,
            _can_manage_waivers=False,
            _can_manage_players=False,
            _can_change_team_name=False,
            _can_add_players=False,
            _can_remove_players=False,
        )

    async def get_team_waivers(self, game: dto.Game, team: dto.Team) -> list[dto.Waiver]:
        return [w for w in self.waivers if w.team.id == team.id and w.game.id == game.id]

    async def upsert(self, waiver: dto.Waiver) -> None:
        for i, existing in enumerate(self.waivers):
            if existing.player.id == waiver.player.id and existing.team.id == waiver.team.id:
                self.waivers[i] = waiver
                return
        self.waivers.append(waiver)

    async def delete(self, waiver: dto.WaiverQuery) -> None:
        self.waivers = [
            w
            for w in self.waivers
            if not (w.player.id == waiver.player.id and w.team.id == waiver.team.id)
        ]

    async def commit(self) -> None:
        self.committed += 1


def admin_identity() -> MockIdentityProvider:
    admin = make_player(99)
    return MockIdentityProvider(player=admin, superuser=admin)


def make_dao() -> FakeWaiverDao:
    team = make_team(2)
    harry = make_player(3)
    draco = make_player(4)
    return FakeWaiverDao(
        game=make_game(),
        team=team,
        players={harry.id: harry, draco.id: draco},
        team_of={harry.id: team.id},
    )


@pytest.mark.asyncio
async def test_admin_signs_a_player_up():
    dao = make_dao()
    interactor = AdminAddWaiverInteractor(dao=dao)

    result = await interactor(
        identity=admin_identity(), game_id=dao.game.id, team_id=dao.team.id, player_id=3
    )

    assert result.team.id == dao.team.id
    assert [(w.player.id, w.played) for w in result.waivers] == [(3, Played.yes)]
    assert dao.committed == 1


@pytest.mark.asyncio
async def test_signing_a_player_up_twice_rewrites_the_waiver():
    """How the panel turns a `no` into a `yes` without a second endpoint."""
    dao = make_dao()
    interactor = AdminAddWaiverInteractor(dao=dao)

    await interactor(
        identity=admin_identity(),
        game_id=dao.game.id,
        team_id=dao.team.id,
        player_id=3,
        played=Played.no,
    )
    result = await interactor(
        identity=admin_identity(),
        game_id=dao.game.id,
        team_id=dao.team.id,
        player_id=3,
        played=Played.yes,
    )

    assert [(w.player.id, w.played) for w in result.waivers] == [(3, Played.yes)]


@pytest.mark.asyncio
async def test_a_player_of_another_team_cant_be_signed_up():
    """A waiver for somebody who plays elsewhere would never show in the roster
    anyway — it is read through the current membership."""
    dao = make_dao()
    interactor = AdminAddWaiverInteractor(dao=dao)

    with pytest.raises(exceptions.PlayerNotInTeam):
        await interactor(
            identity=admin_identity(), game_id=dao.game.id, team_id=dao.team.id, player_id=4
        )

    assert dao.waivers == []
    assert dao.committed == 0


@pytest.mark.asyncio
async def test_admin_removes_a_waiver():
    dao = make_dao()
    await AdminAddWaiverInteractor(dao=dao)(
        identity=admin_identity(), game_id=dao.game.id, team_id=dao.team.id, player_id=3
    )

    await AdminRemoveWaiverInteractor(dao=dao)(
        identity=admin_identity(), game_id=dao.game.id, team_id=dao.team.id, player_id=3
    )

    # the row goes rather than turning into a `revoked` one: unlike the
    # captain's revoke, an admin undoing a mistake leaves the player free to
    # be signed up again
    assert dao.waivers == []


@pytest.mark.asyncio
async def test_only_a_superuser_may_edit_waivers():
    dao = make_dao()
    stranger = MockIdentityProvider(player=make_player(2))

    with pytest.raises(exceptions.NotAuthorizedForAdmin):
        await AdminAddWaiverInteractor(dao=dao)(
            identity=stranger, game_id=dao.game.id, team_id=dao.team.id, player_id=3
        )
    with pytest.raises(exceptions.NotAuthorizedForAdmin):
        await AdminRemoveWaiverInteractor(dao=dao)(
            identity=stranger, game_id=dao.game.id, team_id=dao.team.id, player_id=3
        )
    assert dao.waivers == []
