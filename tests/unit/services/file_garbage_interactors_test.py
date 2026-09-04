from collections.abc import Collection
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import pytest

from shvatka.core.files.dto import GameFileLink
from shvatka.core.files.interactors import (
    STORAGE_ORPHAN_MIN_AGE,
    CollectFileGarbageInteractor,
)
from shvatka.core.models import dto
from shvatka.core.models.dto import hints
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_utc
from tests.fixtures.identity import MockIdentityProvider

ADMIN = dto.Player(id=1, can_be_author=True, is_dummy=False, username="admin")


def make_meta(guid: str, path: str | None = None) -> hints.VerifiableFileMeta:
    return hints.VerifiableFileMeta(
        file_content_link=hints.FileContentLink(file_path=path or f"/files/{guid}"),
        guid=guid,
        original_filename=guid,
        extension="",
        author_id=ADMIN.id,
    )


@dataclass
class FakeGarbageDao:
    links: list[GameFileLink] = field(default_factory=list)
    guids_by_id: dict[int, str] = field(default_factory=dict)
    unlinked: list[hints.VerifiableFileMeta] = field(default_factory=list)
    release_guids: dict[int, set[str]] = field(default_factory=dict)
    paths_by_guid: dict[str, str] = field(default_factory=dict)
    deleted_links: list[int] = field(default_factory=list)
    deleted_metas: list[str] = field(default_factory=list)
    committed: int = 0

    async def get_release_guids(self) -> dict[int, set[str]]:
        return self.release_guids

    async def get_unused_game_file_links(self) -> list[GameFileLink]:
        return list(self.links)

    async def get_guids_by_ids(self, file_ids: Collection[int]) -> dict[int, str]:
        return {id_: self.guids_by_id[id_] for id_ in file_ids if id_ in self.guids_by_id}

    async def delete_game_file_links(self, ids: Collection[int]) -> None:
        self.deleted_links.extend(ids)

    async def get_unlinked_file_metas(
        self, ignored_game_link_ids: Collection[int] = ()
    ) -> list[hints.VerifiableFileMeta]:
        return list(self.unlinked)

    async def delete_file_metas(self, guids: Collection[str]) -> None:
        self.deleted_metas.extend(guids)

    async def get_paths_by_guid(self) -> dict[str, str]:
        return dict(self.paths_by_guid)

    async def commit(self) -> None:
        self.committed += 1


@dataclass
class FakeStorage:
    files: dict[str, datetime] = field(default_factory=dict)
    deleted: list[str] = field(default_factory=list)

    async def list_files(self) -> list[hints.StoredFile]:
        return [
            hints.StoredFile(link=hints.FileContentLink(file_path=path), modified_at=modified_at)
            for path, modified_at in self.files.items()
        ]

    async def delete(self, file_link: hints.FileContentLink) -> None:
        self.deleted.append(file_link.file_path)
        self.files.pop(file_link.file_path, None)


def old() -> datetime:
    return datetime.now(tz=tz_utc) - STORAGE_ORPHAN_MIN_AGE - timedelta(hours=1)


@pytest.mark.asyncio
async def test_collects_unused_link_meta_and_content():
    dao = FakeGarbageDao(
        links=[GameFileLink(id=7, game_id=1, file_id=42)],
        guids_by_id={42: "guid"},
        unlinked=[make_meta("guid")],
        paths_by_guid={"guid": "/files/guid"},
    )
    storage = FakeStorage(files={"/files/guid": old()})
    interactor = CollectFileGarbageInteractor(dao=dao, storage=storage)

    garbage = await interactor(MockIdentityProvider(superuser=ADMIN))

    assert dao.deleted_links == [7]
    assert dao.deleted_metas == ["guid"]
    assert storage.deleted == ["/files/guid"]
    assert dao.committed == 1
    assert garbage.game_links == [GameFileLink(id=7, game_id=1, file_id=42)]
    assert garbage.file_guids == ["guid"]
    assert garbage.stored_files == ["/files/guid"]
    assert garbage.dry_run is False


@pytest.mark.asyncio
async def test_dry_run_reports_the_same_and_deletes_nothing():
    dao = FakeGarbageDao(
        links=[GameFileLink(id=7, game_id=1, file_id=42)],
        guids_by_id={42: "guid"},
        unlinked=[make_meta("guid")],
        paths_by_guid={"guid": "/files/guid"},
    )
    storage = FakeStorage(files={"/files/guid": old()})
    interactor = CollectFileGarbageInteractor(dao=dao, storage=storage)

    garbage = await interactor(MockIdentityProvider(superuser=ADMIN), dry_run=True)

    assert garbage.game_links == [GameFileLink(id=7, game_id=1, file_id=42)]
    assert garbage.file_guids == ["guid"]
    # the meta is only going to be deleted, so its content is garbage as well
    assert garbage.stored_files == ["/files/guid"]
    assert garbage.dry_run is True
    assert dao.deleted_links == []
    assert dao.deleted_metas == []
    assert storage.deleted == []
    assert dao.committed == 0


@pytest.mark.asyncio
async def test_keeps_files_a_release_refers_to():
    dao = FakeGarbageDao(
        links=[GameFileLink(id=7, game_id=1, file_id=42)],
        guids_by_id={42: "banner"},
        unlinked=[make_meta("banner")],
        release_guids={1: {"banner"}},
        paths_by_guid={"banner": "/files/banner"},
    )
    storage = FakeStorage(files={"/files/banner": old()})
    interactor = CollectFileGarbageInteractor(dao=dao, storage=storage)

    garbage = await interactor(MockIdentityProvider(superuser=ADMIN))

    assert garbage.game_links == []
    assert garbage.file_guids == []
    assert garbage.stored_files == []
    assert storage.deleted == []


@pytest.mark.asyncio
async def test_keeps_just_written_content():
    dao = FakeGarbageDao(paths_by_guid={"other": "/files/other"})
    storage = FakeStorage(
        files={"/files/other": old(), "/files/uploading": datetime.now(tz=tz_utc)}
    )
    interactor = CollectFileGarbageInteractor(dao=dao, storage=storage)

    garbage = await interactor(MockIdentityProvider(superuser=ADMIN))

    assert garbage.stored_files == []
    assert storage.deleted == []


@pytest.mark.asyncio
async def test_keeps_content_a_surviving_meta_shares():
    dao = FakeGarbageDao(
        unlinked=[make_meta("copy", path="/files/shared")],
        paths_by_guid={"copy": "/files/shared", "original": "/files/shared"},
    )
    storage = FakeStorage(files={"/files/shared": old()})
    interactor = CollectFileGarbageInteractor(dao=dao, storage=storage)

    garbage = await interactor(MockIdentityProvider(superuser=ADMIN))

    assert garbage.file_guids == ["copy"]
    assert garbage.stored_files == []
    assert storage.deleted == []


@pytest.mark.asyncio
async def test_forbidden_for_non_superuser():
    interactor = CollectFileGarbageInteractor(dao=FakeGarbageDao(), storage=FakeStorage())

    with pytest.raises(exceptions.NotAuthorizedForAdmin):
        await interactor(MockIdentityProvider())
