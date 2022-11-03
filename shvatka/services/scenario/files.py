from io import BytesIO

from shvatka.clients.file_storage import FileStorage
from shvatka.dal.game import GameUpserter
from shvatka.models import dto
from shvatka.models.dto.scn import FileContent


async def upsert_files(
    author: dto.Player, contents: dict[str, BytesIO], files: list[FileContent],
    dao: GameUpserter, file_storage: FileStorage
) -> set[str]:
    guids = set()
    for file in files:
        await dao.check_author_can_own_guid(author, file.guid)
        file_link = await file_storage.put(file, contents[file.guid])
        file.file_content_link = file_link
        await dao.upsert_file(file, author)
        guids.add(file.guid)
    return guids
