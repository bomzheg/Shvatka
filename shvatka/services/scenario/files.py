from typing.io import BinaryIO

from shvatka.interfaces.clients.file_storage import FileStorage
from shvatka.interfaces.dal.game import GameUpserter, GamePackager
from shvatka.models import dto
from shvatka.models.dto import scn
from shvatka.models.dto.scn import FileMeta
from shvatka.utils.exceptions import NotAuthorizedForEdit


async def upsert_files(
    author: dto.Player, contents: dict[str, BinaryIO], files: list[scn.UploadedFileMeta],
    dao: GameUpserter, file_storage: FileStorage,
) -> set[str]:
    guids = set()
    for file in files:
        await dao.check_author_can_own_guid(author, file.guid)
        stored_file = await file_storage.put(file, contents[file.guid])
        await dao.upsert_file(stored_file, author)
        guids.add(file.guid)
    return guids


async def get_file_metas(guids: list[str], author: dto.Player, dao: GamePackager) -> list[FileMeta]:
    file_metas = []
    for guid in guids:
        file_meta = await dao.get_by_guid(guid)
        if file_meta.author_id != author.id:
            raise NotAuthorizedForEdit(
                permission_name="file_edit",
                player=author,
                notify_user="невозможно открыть этот файл",
            )
        file_metas.append(file_meta)
    return file_metas


async def get_file_contents(file_metas: list[FileMeta], file_storage: FileStorage) -> dict[str, BinaryIO]:
    contents = {}
    for file_meta in file_metas:
        content = await file_storage.get(file_meta.file_content_link)
        contents[file_meta.guid] = content
    return contents
