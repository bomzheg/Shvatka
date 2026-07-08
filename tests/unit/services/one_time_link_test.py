import pytest

from shvatka.common.config.models.main import WebConfig
from shvatka.common.url_factory import UrlFactory
from shvatka.core.models import dto
from shvatka.core.services.one_time_link import GenerateOneTimeLoginLinkInteractor
from shvatka.core.utils import exceptions


class FakeIdentity:
    def __init__(self, player: dto.Player | None) -> None:
        self.player = player

    async def get_required_player(self) -> dto.Player:
        if self.player is None:
            raise exceptions.PlayerNotFoundError
        return self.player


class FakeTokenCreator:
    def __init__(self) -> None:
        self.saved: list[dict] = []

    async def save_new_token(self, **dct: dict) -> str:
        self.saved.append(dct["dct"])
        return "the-token"


@pytest.mark.asyncio
async def test_generates_link_for_current_player():
    player = dto.Player(id=1, can_be_author=False, is_dummy=False, username="harry")
    token_creator = FakeTokenCreator()
    interactor = GenerateOneTimeLoginLinkInteractor(
        token_creator=token_creator,
        url_factory=UrlFactory(
            config=WebConfig(
                base_url="https://example.com",
            )
        ),
    )
    identity = FakeIdentity(player)

    url = await interactor(identity=identity)

    assert url == "https://example.com/auth/one-time-token?token=the-token"
    assert token_creator.saved == [{"player_id": 1}]


@pytest.mark.asyncio
async def test_requires_a_player():
    interactor = GenerateOneTimeLoginLinkInteractor(
        token_creator=FakeTokenCreator(),
        url_factory=UrlFactory(
            config=WebConfig(
                base_url="https://example.com",
            )
        ),
    )
    identity = FakeIdentity(None)

    with pytest.raises(exceptions.PlayerNotFoundError):
        await interactor(identity=identity)
