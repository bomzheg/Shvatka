from dataclasses import dataclass, field
from io import BytesIO
from typing import BinaryIO

import pytest

from shvatka.core.games.editor_interactors import UploadGameFileInteractor
from shvatka.core.models import dto
from shvatka.core.models.dto import GameResults, hints
from shvatka.core.models.enums import GameStatus
from shvatka.core.utils.exceptions import FileRejectedByTelegram
from tests.fixtures.identity import MockIdentityProvider
from tests.mocks.file_storage import MemoryFileStorage

AUTHOR = dto.Player(id=1, can_be_author=True, is_dummy=False, username="author")
GAME = dto.Game(
    id=10,
    author=AUTHOR,
    name="my game",
    status=GameStatus.underconstruction,
    manage_token="token",
    start_at=None,
    number=None,
    results=GameResults(published_chanel_id=None, results_picture_file_id=None, keys_url=None),
)


@dataclass
class FakeUploaderDao:
    saved: hints.SavedFileMeta | None = None
    game_files: list[int] = field(default_factory=list)
    committed: int = 0

    async def get_by_id(self, id_: int, author: dto.Player | None = None) -> dto.Game:
        return GAME

    async def upsert(self, file: hints.FileMeta, author: dto.Player) -> hints.SavedFileMeta:
        self.saved = hints.SavedFileMeta(
            id=7,
            author=author,
            author_id=author.id,
            guid=file.guid,
            original_filename=file.original_filename,
            extension=file.extension,
            file_content_link=file.file_content_link,
            content_type=file.content_type,
            file_id=file.file_id,
        )
        return self.saved

    async def add_game_file(self, game_id: int, file_id: int) -> None:
        self.game_files.append(file_id)

    async def commit(self) -> None:
        self.committed += 1


class FakeFileGateway:
    def __init__(self, refuses: bool) -> None:
        self.refuses = refuses
        self.sent: list[str] = []

    async def put(
        self, file_meta: hints.UploadedFileMeta, content: BinaryIO, author: dto.Player
    ) -> None:
        raise NotImplementedError

    async def get(self, file_link: hints.FileMeta) -> BinaryIO:
        raise NotImplementedError

    async def renew_file_id(self, author: dto.Player, file_meta: hints.SavedFileMeta) -> None:
        self.sent.append(file_meta.guid)
        if self.refuses:
            raise FileRejectedByTelegram(guid=file_meta.guid, filename=file_meta.public_filename)


def make_interactor(dao: FakeUploaderDao, gateway: FakeFileGateway) -> UploadGameFileInteractor:
    return UploadGameFileInteractor(
        storage=MemoryFileStorage(),
        dao=dao,
        file_gateway=gateway,
    )


@pytest.mark.asyncio
async def test_uploaded_file_is_sent_to_telegram() -> None:
    dao = FakeUploaderDao()
    gateway = FakeFileGateway(refuses=False)

    saved = await make_interactor(dao, gateway)(
        game_id=GAME.id,
        content=BytesIO(b"content"),
        original_filename="hint.jpg",
        identity=MockIdentityProvider(player=AUTHOR),
    )

    assert gateway.sent == [saved.guid]
    assert dao.game_files == [saved.id]
    assert dao.committed == 1


@pytest.mark.asyncio
async def test_file_telegram_refuses_is_not_kept() -> None:
    dao = FakeUploaderDao()
    gateway = FakeFileGateway(refuses=True)

    with pytest.raises(FileRejectedByTelegram):
        await make_interactor(dao, gateway)(
            game_id=GAME.id,
            content=BytesIO(b"content"),
            original_filename="hint.jpg",
            identity=MockIdentityProvider(player=AUTHOR),
        )

    assert dao.committed == 0


@pytest.mark.asyncio
async def test_force_keeps_the_file_telegram_refused() -> None:
    dao = FakeUploaderDao()
    gateway = FakeFileGateway(refuses=True)

    saved = await make_interactor(dao, gateway)(
        game_id=GAME.id,
        content=BytesIO(b"content"),
        original_filename="hint.jpg",
        identity=MockIdentityProvider(player=AUTHOR),
        force=True,
    )

    assert saved.file_id is None
    assert dao.game_files == [saved.id]
    assert dao.committed == 1
