from collections.abc import Collection
from dataclasses import dataclass, field

import pytest

from shvatka.core.games.release_interactors import (
    DeleteGameReleaseInteractor,
    GameReleaseAnnouncer,
    GetGameReleaseInteractor,
    SaveGameReleaseInteractor,
)
from shvatka.core.models import dto
from shvatka.core.models.dto import GameResults, hints
from shvatka.core.models.enums import GameStatus
from shvatka.core.utils import exceptions
from shvatka.core.views.game import GameReleasePublisher
from tests.fixtures.identity import MockIdentityProvider

BANNER_GUID = "banner-guid"
CHANNEL_ID = -100500


def make_player(id_: int) -> dto.Player:
    return dto.Player(id=id_, can_be_author=True, is_dummy=False, username=f"player{id_}")


def make_game(author: dto.Player, status: GameStatus = GameStatus.ready) -> dto.Game:
    return dto.Game(
        id=10,
        author=author,
        name="my game",
        status=status,
        manage_token="token",
        start_at=None,
        number=None,
        results=GameResults(published_chanel_id=None, results_picture_file_id=None, keys_url=None),
    )


def make_banner(caption: str = "тема игры") -> hints.PhotoHint:
    return hints.PhotoHint(file_guid=BANNER_GUID, caption=caption)


def make_release(
    hints_: list[hints.AnyHint],
    banner: hints.PhotoHint | None = None,
) -> dto.GameRelease:
    return dto.GameRelease(game_id=10, banner=banner, hints=hints_)


@dataclass
class FakeReleaseDao:
    """In-memory stand-in for the release reader/editor protocols."""

    game: dto.Game
    release: dto.GameRelease | None = None
    linked_files: list[int] = field(default_factory=list)
    checked_guids: list[str] = field(default_factory=list)
    committed: int = 0

    async def get_by_id(self, id_: int, author: dto.Player | None = None) -> dto.Game:
        return self.game

    async def get_full(self, id_: int) -> dto.FullGame:
        raise NotImplementedError

    async def add_levels(self, game: dto.Game) -> dto.FullGame:
        raise NotImplementedError

    async def get_release(self, game_id: int) -> dto.GameRelease | None:
        return self.release

    async def save_release(
        self, game: dto.Game, banner: hints.PhotoHint | None, hints_: list[hints.AnyHint]
    ) -> None:
        self.release = dto.GameRelease(game_id=10, banner=banner, hints=hints_)

    async def delete_release(self, game: dto.Game) -> None:
        self.release = None

    async def check_author_can_own_guid(self, author: dto.Player, guid: str) -> None:
        self.checked_guids.append(guid)

    async def get_ids_by_guids(self, guids: Collection[str]) -> list[int]:
        return [1 for _ in guids]

    async def add_game_files(self, game_id: int, file_ids: Collection[int]) -> None:
        self.linked_files.extend(file_ids)

    async def commit(self) -> None:
        self.committed += 1


class RecordingPublisher(GameReleasePublisher):
    """A stand-in for the announcing view, recording what it was asked to show.

    Like the real one it remembers on its own whether it is showing anything —
    the domain never tells it, and never asks.
    """

    def __init__(self) -> None:
        self.posted: list[dto.GameRelease] = []
        self.edited: list[dto.GameRelease] = []
        self.unpublished: list[int] = []
        self.showing = False

    async def publish(self, game: dto.Game, release: dto.GameRelease) -> None:
        if self.showing:
            self.edited.append(release)
            return
        self.showing = True
        self.posted.append(release)

    async def update(self, game: dto.Game, release: dto.GameRelease) -> None:
        if not self.showing:
            return
        self.edited.append(release)

    async def unpublish(self, game: dto.Game) -> None:
        if not self.showing:
            return
        self.showing = False
        self.unpublished.append(game.id)


def make_interactor(
    dao: FakeReleaseDao, publisher: RecordingPublisher
) -> SaveGameReleaseInteractor:
    return SaveGameReleaseInteractor(
        dao=dao, announcer=GameReleaseAnnouncer(dao=dao, publisher=publisher)
    )


@pytest.mark.asyncio
async def test_release_written_before_waivers_waits_for_them():
    author = make_player(1)
    dao = FakeReleaseDao(game=make_game(author, GameStatus.ready))
    publisher = RecordingPublisher()

    release = await make_interactor(dao, publisher)(
        game_id=10,
        banner=make_banner(),
        hints_=[hints.TextHint(text="карта района")],
        identity=MockIdentityProvider(player=author),
    )

    assert release.banner is not None
    assert len(release.hints) == 1
    # the banner leads the release wherever it is shown
    assert release.parts[0] == release.banner
    assert publisher.posted == []
    # the files it references became usable in the game
    assert dao.checked_guids == [BANNER_GUID]
    assert dao.linked_files == [1]


@pytest.mark.asyncio
async def test_release_written_while_collecting_waivers_goes_out_at_once():
    author = make_player(1)
    dao = FakeReleaseDao(game=make_game(author, GameStatus.getting_waivers))
    publisher = RecordingPublisher()

    await make_interactor(dao, publisher)(
        game_id=10,
        banner=None,
        hints_=[hints.TextHint(text="тема игры")],
        identity=MockIdentityProvider(player=author),
    )

    assert len(publisher.posted) == 1


@pytest.mark.asyncio
async def test_release_written_after_the_game_started_is_only_stored():
    author = make_player(1)
    dao = FakeReleaseDao(game=make_game(author, GameStatus.started))
    publisher = RecordingPublisher()

    await make_interactor(dao, publisher)(
        game_id=10,
        banner=None,
        hints_=[hints.TextHint(text="тема игры")],
        identity=MockIdentityProvider(player=author),
    )

    assert publisher.posted == []


@pytest.mark.asyncio
async def test_editing_a_published_release_edits_it_in_the_channel():
    author = make_player(1)
    dao = FakeReleaseDao(
        game=make_game(author, GameStatus.started),
        release=make_release([hints.TextHint(text="старая тема")]),
    )
    publisher = RecordingPublisher()
    publisher.showing = True  # the channel already carries this release

    await make_interactor(dao, publisher)(
        game_id=10,
        banner=None,
        hints_=[hints.TextHint(text="новая тема")],
        identity=MockIdentityProvider(player=author),
    )

    assert publisher.posted == []
    assert len(publisher.edited) == 1


@pytest.mark.asyncio
async def test_release_of_a_finished_game_is_still_editable():
    author = make_player(1)
    dao = FakeReleaseDao(game=make_game(author, GameStatus.finished))

    release = await make_interactor(dao, RecordingPublisher())(
        game_id=10,
        banner=None,
        hints_=[hints.TextHint(text="тема игры")],
        identity=MockIdentityProvider(player=author),
    )

    assert release.hints
    assert dao.release is not None


@pytest.mark.asyncio
async def test_release_of_a_complete_game_is_admin_only():
    author = make_player(1)
    dao = FakeReleaseDao(game=make_game(author, GameStatus.complete))

    with pytest.raises(exceptions.NotAuthorizedForEdit):
        await make_interactor(dao, RecordingPublisher())(
            game_id=10,
            banner=None,
            hints_=[hints.TextHint(text="тема игры")],
            identity=MockIdentityProvider(player=author),
        )
    assert dao.release is None


@pytest.mark.asyncio
async def test_admin_edits_the_release_of_a_complete_game():
    admin = make_player(2)
    dao = FakeReleaseDao(game=make_game(make_player(1), GameStatus.complete))

    release = await make_interactor(dao, RecordingPublisher())(
        game_id=10,
        banner=None,
        hints_=[hints.TextHint(text="тема игры")],
        identity=MockIdentityProvider(player=admin, superuser=admin),
    )

    assert release.hints


@pytest.mark.asyncio
async def test_release_of_another_author_is_not_editable():
    dao = FakeReleaseDao(game=make_game(make_player(1)))
    publisher = RecordingPublisher()

    with pytest.raises(exceptions.NotAuthorizedForEdit):
        await make_interactor(dao, publisher)(
            game_id=10,
            banner=None,
            hints_=[hints.TextHint(text="тема игры")],
            identity=MockIdentityProvider(player=make_player(2)),
        )
    assert dao.release is None
    assert publisher.posted == []


@pytest.mark.asyncio
async def test_a_stored_release_is_readable_by_anyone():
    author = make_player(1)
    dao = FakeReleaseDao(game=make_game(author), release=make_release([hints.TextHint(text="а")]))

    assert await GetGameReleaseInteractor(dao=dao)(game_id=10) is not None


@pytest.mark.asyncio
async def test_no_release_reads_as_none():
    dao = FakeReleaseDao(game=make_game(make_player(1)))

    assert await GetGameReleaseInteractor(dao=dao)(game_id=10) is None


@pytest.mark.asyncio
async def test_deleting_a_published_release_takes_it_out_of_the_channel():
    author = make_player(1)
    dao = FakeReleaseDao(
        game=make_game(author),
        release=make_release([hints.TextHint(text="а")]),
    )
    publisher = RecordingPublisher()
    publisher.showing = True
    interactor = DeleteGameReleaseInteractor(
        dao=dao, announcer=GameReleaseAnnouncer(dao=dao, publisher=publisher)
    )

    await interactor(game_id=10, identity=MockIdentityProvider(player=author))

    assert dao.release is None
    assert dao.committed == 1
    assert len(publisher.unpublished) == 1


@pytest.mark.asyncio
async def test_a_release_may_be_just_a_banner():
    """The banner alone is a release — the site can show it above the header."""
    author = make_player(1)
    dao = FakeReleaseDao(game=make_game(author, GameStatus.getting_waivers))

    release = await make_interactor(dao, RecordingPublisher())(
        game_id=10,
        banner=make_banner(),
        hints_=[],
        identity=MockIdentityProvider(player=author),
    )

    assert release.banner is not None
    assert release.hints == []
    assert not release.is_empty
    assert release.get_guids() == [BANNER_GUID]


@pytest.mark.asyncio
async def test_dropping_the_banner_keeps_the_rest_of_the_release():
    author = make_player(1)
    dao = FakeReleaseDao(
        game=make_game(author, GameStatus.ready),
        release=make_release([hints.TextHint(text="тема")], banner=make_banner()),
    )

    release = await make_interactor(dao, RecordingPublisher())(
        game_id=10,
        banner=None,
        hints_=[hints.TextHint(text="тема")],
        identity=MockIdentityProvider(player=author),
    )

    assert release.banner is None
    assert len(release.parts) == 1


@pytest.mark.asyncio
async def test_announcing_a_game_without_a_release_does_nothing():
    dao = FakeReleaseDao(game=make_game(make_player(1), GameStatus.getting_waivers))
    publisher = RecordingPublisher()

    await GameReleaseAnnouncer(dao=dao, publisher=publisher).announce(dao.game)

    assert publisher.posted == []
