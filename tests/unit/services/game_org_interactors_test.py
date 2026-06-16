from dataclasses import dataclass, field

import pytest

from shvatka.core.games.org_interactors import (
    AddGameOrgInteractor,
    ChangeOrgPermissionInteractor,
    ListGameOrgsInteractor,
    RemoveGameOrgInteractor,
)
from shvatka.core.models import dto
from shvatka.core.models.dto import GameResults
from shvatka.core.models.enums import GameStatus, OrgPermission
from shvatka.core.utils import exceptions
from tests.fixtures.identity import MockIdentityProvider


def make_player(id_: int) -> dto.Player:
    return dto.Player(id=id_, can_be_author=True, is_dummy=False, username=f"player{id_}")


def make_game(id_: int, author: dto.Player, status: GameStatus) -> dto.Game:
    return dto.Game(
        id=id_,
        author=author,
        name=f"game{id_}",
        status=status,
        manage_token="token",
        start_at=None,
        number=None,
        results=GameResults(published_chanel_id=None, results_picture_file_id=None, keys_url=None),
    )


@dataclass
class FakeOrgDao:
    """In-memory stand-in for the organizer DAO covering the protocols we need."""

    game: dto.Game
    orgs: dict[int, dto.SecondaryOrganizer] = field(default_factory=dict)
    _seq: int = 0
    committed: int = 0

    def add(self, player: dto.Player, *, deleted: bool = False) -> dto.SecondaryOrganizer:
        self._seq += 1
        org = dto.SecondaryOrganizer(
            id=self._seq,
            player=player,
            game=self.game,
            can_spy=False,
            can_see_log_keys=False,
            can_validate_waivers=False,
            view_scenario=False,
            deleted=deleted,
        )
        self.orgs[org.id] = org
        return org

    async def get_orgs(
        self, game: dto.Game, with_deleted: bool = False
    ) -> list[dto.SecondaryOrganizer]:
        return [o for o in self.orgs.values() if with_deleted or not o.deleted]

    async def add_new_org(self, game: dto.Game, player: dto.Player) -> dto.SecondaryOrganizer:
        return self.add(player)

    async def get_by_player_or_none(
        self, game: dto.Game, player: dto.Player
    ) -> dto.SecondaryOrganizer | None:
        for org in self.orgs.values():
            if org.player.id == player.id:
                return org
        return None

    async def get_by_id(self, id_: int) -> dto.SecondaryOrganizer:
        return self.orgs[id_]

    async def flip_permission(
        self, org: dto.SecondaryOrganizer, permission: OrgPermission
    ) -> None:
        stored = self.orgs[org.id]
        setattr(stored, permission.name, not getattr(stored, permission.name))

    async def flip_deleted(self, org: dto.SecondaryOrganizer) -> None:
        stored = self.orgs[org.id]
        stored.deleted = not stored.deleted

    async def commit(self) -> None:
        self.committed += 1


@dataclass
class FakeGameDao:
    games: dict[int, dto.Game]

    async def get_by_id(self, id_: int, author: dto.Player | None = None) -> dto.Game:
        return self.games[id_]


@dataclass
class FakePlayerDao:
    players: dict[int, dto.Player]

    async def get_by_id(self, id_: int) -> dto.Player:
        return self.players[id_]


@pytest.fixture
def author() -> dto.Player:
    return make_player(1)


@pytest.fixture
def stranger() -> dto.Player:
    return make_player(2)


@pytest.mark.asyncio
async def test_list_returns_primary_and_secondary(author: dto.Player, stranger: dto.Player):
    game = make_game(10, author, GameStatus.underconstruction)
    org_dao = FakeOrgDao(game=game)
    secondary = org_dao.add(stranger)
    deleted = org_dao.add(make_player(3), deleted=True)
    identity = MockIdentityProvider(
        player=author, organizer={game.id: dto.PrimaryOrganizer(player=author, game=game)}
    )

    interactor = ListGameOrgsInteractor(game_dao=FakeGameDao({game.id: game}), org_dao=org_dao)
    result = await interactor(game_id=game.id, identity=identity)

    ids = [getattr(o, "id", None) for o in result]
    # primary (None) + both secondary orgs, including the deleted one
    assert ids == [None, secondary.id, deleted.id]
    assert result[0].player.id == author.id


@pytest.mark.asyncio
async def test_list_forbidden_for_stranger(author: dto.Player, stranger: dto.Player):
    game = make_game(10, author, GameStatus.underconstruction)
    identity = MockIdentityProvider(player=stranger, organizer={game.id: None})

    interactor = ListGameOrgsInteractor(
        game_dao=FakeGameDao({game.id: game}), org_dao=FakeOrgDao(game=game)
    )
    with pytest.raises(exceptions.IsNotOrganizer):
        await interactor(game_id=game.id, identity=identity)


@pytest.mark.asyncio
async def test_list_public_when_completed(author: dto.Player, stranger: dto.Player):
    game = make_game(10, author, GameStatus.complete)
    identity = MockIdentityProvider(player=stranger, organizer={game.id: None})

    interactor = ListGameOrgsInteractor(
        game_dao=FakeGameDao({game.id: game}), org_dao=FakeOrgDao(game=game)
    )
    result = await interactor(game_id=game.id, identity=identity)
    assert [o.player.id for o in result] == [author.id]


@pytest.mark.asyncio
async def test_add_org(author: dto.Player, stranger: dto.Player):
    game = make_game(10, author, GameStatus.underconstruction)
    org_dao = FakeOrgDao(game=game)
    interactor = AddGameOrgInteractor(
        game_dao=FakeGameDao({game.id: game}),
        player_dao=FakePlayerDao({stranger.id: stranger}),
        org_getter=org_dao,
        org_adder=org_dao,
    )

    org = await interactor(
        game_id=game.id, player_id=stranger.id, identity=MockIdentityProvider(player=author)
    )
    assert org.player.id == stranger.id
    assert org_dao.committed == 1
    assert len(await org_dao.get_orgs(game)) == 1


@pytest.mark.asyncio
async def test_add_org_rejects_non_author(author: dto.Player, stranger: dto.Player):
    game = make_game(10, author, GameStatus.underconstruction)
    org_dao = FakeOrgDao(game=game)
    interactor = AddGameOrgInteractor(
        game_dao=FakeGameDao({game.id: game}),
        player_dao=FakePlayerDao({stranger.id: stranger}),
        org_getter=org_dao,
        org_adder=org_dao,
    )
    with pytest.raises(exceptions.GameHasAnotherAuthor):
        await interactor(
            game_id=game.id, player_id=stranger.id, identity=MockIdentityProvider(player=stranger)
        )


@pytest.mark.asyncio
async def test_add_org_rejects_duplicate(author: dto.Player, stranger: dto.Player):
    game = make_game(10, author, GameStatus.underconstruction)
    org_dao = FakeOrgDao(game=game)
    org_dao.add(stranger)
    interactor = AddGameOrgInteractor(
        game_dao=FakeGameDao({game.id: game}),
        player_dao=FakePlayerDao({stranger.id: stranger}),
        org_getter=org_dao,
        org_adder=org_dao,
    )
    with pytest.raises(exceptions.PlayerAlreadyOrganizer):
        await interactor(
            game_id=game.id, player_id=stranger.id, identity=MockIdentityProvider(player=author)
        )


@pytest.mark.asyncio
async def test_change_permission_is_idempotent(author: dto.Player, stranger: dto.Player):
    game = make_game(10, author, GameStatus.underconstruction)
    org_dao = FakeOrgDao(game=game)
    org = org_dao.add(stranger)
    interactor = ChangeOrgPermissionInteractor(
        game_dao=FakeGameDao({game.id: game}), org_dao=org_dao
    )
    identity = MockIdentityProvider(player=author)

    result = await interactor(
        game_id=game.id,
        org_id=org.id,
        permission=OrgPermission.can_spy,
        value=True,
        identity=identity,
    )
    assert result.can_spy is True
    assert org_dao.committed == 1

    # already True -> no extra flip / commit
    result = await interactor(
        game_id=game.id,
        org_id=org.id,
        permission=OrgPermission.can_spy,
        value=True,
        identity=identity,
    )
    assert result.can_spy is True
    assert org_dao.committed == 1


@pytest.mark.asyncio
async def test_change_permission_wrong_game(author: dto.Player, stranger: dto.Player):
    # org belongs to game 10, but the request targets a different game (20)
    game = make_game(10, author, GameStatus.underconstruction)
    other_game = make_game(20, author, GameStatus.underconstruction)
    org_dao = FakeOrgDao(game=game)
    org = org_dao.add(stranger)
    interactor = ChangeOrgPermissionInteractor(
        game_dao=FakeGameDao({game.id: game, other_game.id: other_game}), org_dao=org_dao
    )
    with pytest.raises(exceptions.GameNotFound):
        await interactor(
            game_id=other_game.id,
            org_id=org.id,
            permission=OrgPermission.can_spy,
            value=True,
            identity=MockIdentityProvider(player=author),
        )


@pytest.mark.asyncio
async def test_remove_org_is_idempotent(author: dto.Player, stranger: dto.Player):
    game = make_game(10, author, GameStatus.underconstruction)
    org_dao = FakeOrgDao(game=game)
    org = org_dao.add(stranger)
    interactor = RemoveGameOrgInteractor(game_dao=FakeGameDao({game.id: game}), org_dao=org_dao)
    identity = MockIdentityProvider(player=author)

    result = await interactor(game_id=game.id, org_id=org.id, identity=identity)
    assert result.deleted is True
    assert org_dao.committed == 1

    # already deleted -> stays deleted, no extra flip
    result = await interactor(game_id=game.id, org_id=org.id, identity=identity)
    assert result.deleted is True
    assert org_dao.committed == 1
