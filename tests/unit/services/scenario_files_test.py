from io import BytesIO
from typing import BinaryIO

import pytest

from shvatka.core.models import dto
from shvatka.core.models.dto import hints
from shvatka.core.services.scenario.files import upsert_files
from shvatka.core.utils.exceptions import FileRejectedByTelegram, FilesCantBeSentToTg


def make_player() -> dto.Player:
    return dto.Player(id=1, can_be_author=True, is_dummy=False, username="author")


def make_file(guid: str) -> hints.UploadedFileMeta:
    return hints.UploadedFileMeta(guid=guid, original_filename=guid, extension=".jpg")


class FakeGuidOwnershipDao:
    async def check_author_can_own_guid(self, author: dto.Player, guid: str) -> None:
        pass


class FakeFileGateway:
    def __init__(self, rejected_guids: set[str]) -> None:
        self.rejected_guids = rejected_guids
        self.put_calls: list[str] = []

    async def put(
        self,
        file_meta: hints.UploadedFileMeta,
        content: BinaryIO,
        author: dto.Player,
    ) -> None:
        self.put_calls.append(file_meta.guid)
        if file_meta.guid in self.rejected_guids:
            raise FileRejectedByTelegram(guid=file_meta.guid, filename=file_meta.public_filename)


@pytest.mark.asyncio
async def test_upsert_files_collects_every_rejection_before_raising() -> None:
    gateway = FakeFileGateway(rejected_guids={"bad-1", "bad-2"})
    files = [make_file("ok"), make_file("bad-1"), make_file("bad-2")]
    contents = {f.guid: BytesIO(b"data") for f in files}

    with pytest.raises(FilesCantBeSentToTg) as exc_info:
        await upsert_files(make_player(), contents, files, FakeGuidOwnershipDao(), gateway)

    assert gateway.put_calls == ["ok", "bad-1", "bad-2"]
    assert {e.guid for e in exc_info.value.errors} == {"bad-1", "bad-2"}


@pytest.mark.asyncio
async def test_upsert_files_returns_guids_of_files_saved_without_errors() -> None:
    gateway = FakeFileGateway(rejected_guids=set())
    files = [make_file("one"), make_file("two")]
    contents = {f.guid: BytesIO(b"data") for f in files}

    guids = await upsert_files(make_player(), contents, files, FakeGuidOwnershipDao(), gateway)

    assert guids == {"one", "two"}


@pytest.mark.asyncio
async def test_upsert_files_keeps_no_guid_of_a_rejected_file() -> None:
    gateway = FakeFileGateway(rejected_guids={"bad"})
    files = [make_file("ok"), make_file("bad")]
    contents = {f.guid: BytesIO(b"data") for f in files}

    with pytest.raises(FilesCantBeSentToTg) as exc_info:
        await upsert_files(make_player(), contents, files, FakeGuidOwnershipDao(), gateway)

    (rejected,) = exc_info.value.errors
    assert rejected.guid == "bad"


@pytest.mark.asyncio
async def test_the_error_names_the_files_by_itself() -> None:
    gateway = FakeFileGateway(rejected_guids={"bad-1", "bad-2"})
    files = [make_file("bad-1"), make_file("bad-2")]
    contents = {f.guid: BytesIO(b"data") for f in files}

    with pytest.raises(FilesCantBeSentToTg) as exc_info:
        await upsert_files(make_player(), contents, files, FakeGuidOwnershipDao(), gateway)

    assert "bad-1.jpg" in str(exc_info.value.notify_user)
    assert "bad-2.jpg" in str(exc_info.value.notify_user)
