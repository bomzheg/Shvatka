import logging
from pathlib import Path
from typing import BinaryIO, Sequence
from uuid import uuid4

from shvatka.core.interfaces.clients.file_storage import FileGateway, FileStorage
from shvatka.core.interfaces.dal.file_info import FileUpserter, GameFilesMetaGetter
from shvatka.core.interfaces.dal.file_link import LevelFilesSyncDao
from shvatka.core.interfaces.dal.game import GameUpserter
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto, enums
from shvatka.core.models.dto import hints
from shvatka.core.utils.exceptions import NotAuthorizedForEdit

logger = logging.getLogger(__name__)


async def sync_files_for_level(level: dto.Level, dao: LevelFilesSyncDao) -> None:
    """Reconcile a level's file links after its scenario was saved.

    ``level_files`` is made to match exactly the files the level references; for a
    level that belongs to a game, those files are additionally registered as
    usable in that game (``game_files``, add-only).
    """
    file_ids = await dao.get_ids_by_guids(level.get_guids())
    await dao.sync_level_files(level.db_id, file_ids)
    if level.game_id is not None:
        await dao.add_game_files(level.game_id, file_ids)


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
    sha256/mime) and saves the resulting meta to the DB. The actual content type is
    derived from the detected mime type.
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
    game: dto.FullGame, identity: IdentityProvider, dao: GameFilesMetaGetter
) -> Sequence[hints.FileMeta]:
    """Files usable in the game — the whole ``game_files`` set, not just the files
    referenced by the current scenario.

    ``game_files`` is expected to be a superset of the scenario's files; if the
    scenario references a file that is not registered there, it is logged as a
    warning (and the file is omitted, since it is not a usable game file).
    """
    metas = await dao.get_metas_by_ids(await dao.get_game_file_ids(game.id))
    available = {meta.guid for meta in metas}
    for guid in game.get_guids():
        if guid not in available:
            logger.warning("game %s references file %s missing from its game_files", game.id, guid)
    file_metas: list[hints.FileMeta] = []
    for meta in metas:
        await check_file_meta_can_read(identity, meta, game)
        file_metas.append(meta)
    return file_metas


async def get_file_contents(
    file_metas: Sequence[hints.FileMeta], file_gateway: FileGateway
) -> dict[str, BinaryIO]:
    contents = {}
    for file_meta in file_metas:
        content = await file_gateway.get(file_meta)
        contents[file_meta.guid] = content
    return contents


async def check_file_meta_can_read(
    identity: IdentityProvider,
    file_meta: hints.VerifiableFileMeta,
    game: dto.Game,
):
    if game.is_complete():
        return
    author = await identity.get_required_player()
    if file_meta.author_id == author.id:
        return
    if org := await identity.get_org(game=game):
        if not org.deleted and org.view_scenario:
            return
    raise NotAuthorizedForEdit(
        permission_name="file_edit",
        player=author,
        notify_user="невозможно открыть этот файл",
    )
