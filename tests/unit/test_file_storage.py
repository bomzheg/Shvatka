import tempfile
from io import BytesIO
from pathlib import Path

import pytest

from clients.file_storage import LocalFileStorage
from common.config.models.main import FileStorageConfig
from tests.fixtures.file_storage_constants import FILE_CONTENT


@pytest.mark.asyncio
async def test_file_storage():
    storage_config = FileStorageConfig(
        path=Path(tempfile.gettempdir()) / "shvatka-files",
        mkdir=True,
        parents=False,
        exist_ok=True,
    )
    file_storage = LocalFileStorage(storage_config)
    saved = await file_storage.put(FILE_CONTENT.local_file_name, BytesIO(b"12345"))
    loaded = await file_storage.get(saved)
    assert loaded.read() == b"12345"
