from dishka import Provider, Scope, provide

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.models import enums
from shvatka.core.models.dto import hints
from tests.fixtures.scn_fixtures import GUID
from tests.mocks.file_storage import MemoryFileStorage

FILE_ID = "98765"
CHAT_ID = 111
FILE_META = hints.FileMeta(
    guid=GUID,
    tg_link=hints.TgLink(file_id=FILE_ID, content_type=enums.HintType.photo),
    extension=".jpg",
    file_content_link=hints.FileContentLink(file_path=GUID + ".jpg"),
    original_filename="файло",
)


class MemoryFileStorageProvider(Provider):
    scope = Scope.APP

    @provide
    def get_file_storage(self) -> FileStorage:
        return MemoryFileStorage()
