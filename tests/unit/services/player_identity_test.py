from dataclasses import dataclass, field

import pytest

from shvatka.core.models import dto
from shvatka.core.models.dto import GameResults
from shvatka.core.models.enums import GameStatus
from shvatka.core.services.identity import PlayerIdentityProvider
from shvatka.core.utils import exceptions


def make_player(id_: int) -> dto.Player:
    return dto.Player(id=id_, can_be_author=True, is_dummy=False, username=f"player{id_}")


def make_game(author: dto.Player) -> dto.Game:
    return dto.Game(
        id=1,
        author=author,
        name="game",
        status=GameStatus.complete,
        manage_token="token",
        start_at=None,
        number=1,
        results=GameResults(published_chanel_id=None, results_picture_file_id=None, keys_url=None),
    )


@dataclass
class FakeOrgDao:
    orgs: dict[int, dto.SecondaryOrganizer] = field(default_factory=dict)
    calls: int = 0

    def add(self, player: dto.Player, game: dto.Game) -> dto.SecondaryOrganizer:
        org = dto.SecondaryOrganizer(
            id=len(self.orgs) + 1,
            player=player,
            game=game,
            can_spy=True,
            can_see_log_keys=True,
            can_validate_waivers=False,
            view_scenario=True,
            deleted=False,
        )
        self.orgs[player.id] = org
        return org

    async def get_by_player(
        self, game: dto.Game, player: dto.Player
    ) -> dto.SecondaryOrganizer:  # pragma: no cover - unused by the provider
        return self.orgs[player.id]

    async def get_by_player_or_none(
        self, game: dto.Game, player: dto.Player
    ) -> dto.SecondaryOrganizer | None:
        self.calls += 1
        return self.orgs.get(player.id)


@pytest.mark.asyncio
async def test_author_is_primary_org():
    author = make_player(1)
    game = make_game(author)
    identity = PlayerIdentityProvider(player=author, dao=FakeOrgDao())

    org = await identity.get_required_org(game)

    assert isinstance(org, dto.PrimaryOrganizer)
    assert org.player == author


@pytest.mark.asyncio
async def test_secondary_org_is_loaded_once():
    author = make_player(1)
    org_player = make_player(2)
    game = make_game(author)
    dao = FakeOrgDao()
    dao.add(org_player, game)
    identity = PlayerIdentityProvider(player=org_player, dao=dao)

    assert await identity.get_org(game) is not None
    assert await identity.get_org(game) is not None
    assert dao.calls == 1


@pytest.mark.asyncio
async def test_stranger_is_not_org():
    author = make_player(1)
    stranger = make_player(3)
    game = make_game(author)
    identity = PlayerIdentityProvider(player=stranger, dao=FakeOrgDao())

    assert await identity.get_org(game) is None
    with pytest.raises(exceptions.IsNotOrganizer):
        await identity.get_required_org(game)


@pytest.mark.asyncio
async def test_has_no_team_and_no_chat():
    player = make_player(1)
    identity = PlayerIdentityProvider(player=player, dao=FakeOrgDao())

    assert await identity.get_required_player() == player
    assert await identity.get_chat() is None
    assert await identity.get_team() is None
    assert await identity.get_full_team_player() is None
    assert not await identity.is_superuser()
