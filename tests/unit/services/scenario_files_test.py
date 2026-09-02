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
    """Refuses the given guids the way telegram would."""

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
    """A rejected file must not stop the loop early.

    Every file is tried, and the raised error covers all the rejected ones, not
    just the first — so the caller can show the whole list at once.
    """
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
    """A refused file is not counted as saved, so the caller's own
    ``check_all_files_saved`` cannot pass on a half-imported package."""
    gateway = FakeFileGateway(rejected_guids={"bad"})
    files = [make_file("ok"), make_file("bad")]
    contents = {f.guid: BytesIO(b"data") for f in files}

    with pytest.raises(FilesCantBeSentToTg) as exc_info:
        await upsert_files(make_player(), contents, files, FakeGuidOwnershipDao(), gateway)

    (rejected,) = exc_info.value.errors
    assert rejected.guid == "bad"


@pytest.mark.asyncio
async def test_the_error_names_the_files_by_itself() -> None:
    """Every edge shows ``notify_user``: on its own it has to say which files,
    or the author is told that something failed and nothing more."""
    gateway = FakeFileGateway(rejected_guids={"bad-1", "bad-2"})
    files = [make_file("bad-1"), make_file("bad-2")]
    contents = {f.guid: BytesIO(b"data") for f in files}

    with pytest.raises(FilesCantBeSentToTg) as exc_info:
        await upsert_files(make_player(), contents, files, FakeGuidOwnershipDao(), gateway)

    assert "bad-1.jpg" in str(exc_info.value.notify_user)
    assert "bad-2.jpg" in str(exc_info.value.notify_user)
