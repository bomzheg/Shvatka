import tempfile
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest

from shvatka.common.config.models.main import FileStorageConfig
from shvatka.core.models.dto import hints
from shvatka.infrastructure.clients.file_storage import LocalFileStorage, detect_mime_type
from tests.fixtures.file_storage import FILE_META


def make_storage() -> LocalFileStorage:
    storage_config = FileStorageConfig(
        path=Path(tempfile.gettempdir()) / "shvatka-files",
        mkdir=True,
        parents=False,
        exist_ok=True,
    )
    return LocalFileStorage(storage_config)


def make_heic_bytes() -> bytes:
    import pillow_heif
    from PIL import Image

    pillow_heif.register_heif_opener()
    image = Image.new("RGB", (32, 24), (200, 50, 50))
    buffer = BytesIO()
    image.save(buffer, format="HEIF")
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_file_storage():
    file_storage = make_storage()
    saved = await file_storage.put_content(FILE_META.local_file_name, BytesIO(b"12345"))
    loaded = await file_storage.get(saved)
    assert loaded.read() == b"12345"


@pytest.mark.asyncio
async def test_put_heic_is_converted_to_jpeg():
    file_storage = make_storage()
    heic = make_heic_bytes()
    assert detect_mime_type(heic) == "image/heic"

    file_meta = hints.UploadedFileMeta(
        guid=str(uuid4()),
        original_filename="photo",
        extension=".heic",
    )
    stored = await file_storage.put(file_meta, BytesIO(heic))

    assert stored.extension == ".jpg"
    assert stored.mime_type == "image/jpeg"
    assert stored.public_filename == "photo.jpg"
    assert stored.file_content_link.file_path.endswith(".jpg")

    content = await file_storage.get(stored.file_content_link)
    assert detect_mime_type(content.read()) == "image/jpeg"
