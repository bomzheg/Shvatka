from pathlib import Path
from typing import BinaryIO, Sequence
from uuid import uuid4

from shvatka.core.interfaces.clients.file_storage import FileGateway, FileStorage
from shvatka.core.interfaces.dal.file_info import FileInfoGetter, FileUpserter
from shvatka.core.interfaces.dal.game import GameUpserter
from shvatka.core.models import dto, enums
from shvatka.core.models.dto import hints
from shvatka.core.utils.exceptions import NotAuthorizedForEdit


_MIME_PREFIX_TO_HINT_TYPE = {
    "image": enums.HintType.photo,
    "video": enums.HintType.video,
    "audio": enums.HintType.audio,
}


def hint_type_by_mime(mime_type: str | None) -> enums.HintType:
    """Best-effort mapping of a detected mime type to a HintType.

    Anything that is not a recognised image/video/audio is treated as a document.
    """
    if mime_type:
        prefix = mime_type.split("/", maxsplit=1)[0]
        if prefix in _MIME_PREFIX_TO_HINT_TYPE:
            return _MIME_PREFIX_TO_HINT_TYPE[prefix]
    return enums.HintType.document


async def save_file(
    author: dto.Player,
    content: BinaryIO,
    original_filename: str,
    storage: FileStorage,
    dao: FileUpserter,
) -> hints.SavedFileMeta:
    """Store a single uploaded file (from the web UI) and persist its FileInfo.

    Generates a fresh guid, stores the content via the file storage (which detects
    sha256/mime and deduplicates) and saves the resulting meta to the DB. The actual
    content type is derived from the detected mime type.
    """
    guid = str(uuid4())
    extension = "".join(Path(original_filename).suffixes)
    name = original_filename[: -len(extension)] if extension else original_filename
    file_meta = hints.UploadedFileMeta(
        guid=guid,
        original_filename=name,
        extension=extension,
    )
    stored = await storage.put(file_meta, content)
    stored.content_type = hint_type_by_mime(stored.mime_type)
    saved = await dao.upsert(stored, author)
    await dao.commit()
    return saved


async def upsert_files(
    author: dto.Player,
    contents: dict[str, BinaryIO],
    files: list[hints.UploadedFileMeta],
    dao: GameUpserter,
    file_gateway: FileGateway,
) -> set[str]:
    guids = set()
    for file in files:
        await dao.check_author_can_own_guid(author, file.guid)
        await file_gateway.put(file, contents[file.guid], author)
        guids.add(file.guid)
    return guids


async def get_file_metas(
    game: dto.FullGame, author: dto.Player, dao: FileInfoGetter
) -> Sequence[hints.FileMeta]:
    file_metas: list[hints.FileMeta] = []
    for guid in game.get_guids():
        file_meta = await dao.get_by_guid(guid)
        check_file_meta_can_read(author, file_meta, game)
        file_metas.append(file_meta)
    return file_metas


async def get_file_contents(
    file_metas: Sequence[hints.FileMeta], file_gateway: FileGateway
) -> dict[str, BinaryIO]:
    contents = {}
    for file_meta in file_metas:
        content = await file_gateway.get(file_meta)
        contents[file_meta.guid] = content
    return contents


async def get_file_content(
    guid: str, file_gateway: FileGateway, author: dto.Player, game: dto.Game, dao: FileInfoGetter
) -> BinaryIO:
    meta = await dao.get_by_guid(guid)
    check_file_meta_can_read(author, meta, game)
    return await file_gateway.get(meta)


def check_file_meta_can_read(
    author: dto.Player, file_meta: hints.VerifiableFileMeta, game: dto.Game
):
    if game.is_complete():
        return
    if file_meta.author_id != author.id:
        raise NotAuthorizedForEdit(
            permission_name="file_edit",
            player=author,
            notify_user="невозможно открыть этот файл",
        )
