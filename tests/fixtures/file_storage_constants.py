from src.core.models import enums
from src.core.models.dto import scn
from tests.fixtures.scn_fixtures import GUID

FILE_ID = "98765"
CHAT_ID = 111
FILE_META = scn.FileMeta(
    guid=GUID,
    tg_link=scn.TgLink(file_id=FILE_ID, content_type=enums.HintType.photo),
    extension=".jpg",
    file_content_link=scn.FileContentLink(file_path=GUID + ".jpg"),
    original_filename="файло",
)
