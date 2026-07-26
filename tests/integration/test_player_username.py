import pytest

from shvatka.core.models import dto
from shvatka.core.services.user import upsert_user
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.player_username_updater import renew_id_usernames
from tests.fixtures.player import create_player


@pytest.mark.asyncio
async def test_username_by_tg_username(dao: HolderDao):
    player = await create_player(
        dto.User(tg_id=101, username="the_chosen_one", first_name="Гарри", last_name="Поттер"),
        dao,
    )
    assert player.username == "the_chosen_one"


@pytest.mark.asyncio
async def test_username_by_transliterated_names(dao: HolderDao):
    player = await create_player(dto.User(tg_id=102, first_name="Гарри", last_name="Поттер"), dao)
    assert player.username == "garri_potter"


@pytest.mark.asyncio
async def test_username_by_first_name_only(dao: HolderDao):
    player = await create_player(dto.User(tg_id=103, first_name="Гарри"), dao)
    assert player.username == "garri"


@pytest.mark.asyncio
async def test_username_by_names_occupied(dao: HolderDao):
    first = await create_player(dto.User(tg_id=104, first_name="Гарри", last_name="Поттер"), dao)
    second = await create_player(dto.User(tg_id=105, first_name="Гарри", last_name="Поттер"), dao)
    assert first.username == "garri_potter"
    assert second.username == "garri_potter_1"


@pytest.mark.asyncio
async def test_username_by_id_without_names(dao: HolderDao):
    player = await create_player(dto.User(tg_id=106), dao)
    assert player.username == f"id{player.id}"


@pytest.mark.asyncio
async def test_renew_id_usernames(dao: HolderDao, check_dao: HolderDao):
    nameless = await create_player(dto.User(tg_id=107), dao)
    with_username = await create_player(dto.User(tg_id=108, username="voldemort_fan"), dao)
    assert nameless.username == f"id{nameless.id}"

    await upsert_user(dto.User(tg_id=107, first_name="Джоан", last_name="Роулинг"), dao.user)
    renamed = await renew_id_usernames(dao)

    assert renamed == [(f"id{nameless.id}", "dzhoan_rouling")]
    assert (await check_dao.player.get_by_id(nameless.id)).username == "dzhoan_rouling"
    assert (await check_dao.player.get_by_id(with_username.id)).username == "voldemort_fan"


@pytest.mark.asyncio
async def test_renew_id_usernames_keeps_nameless_player(dao: HolderDao, check_dao: HolderDao):
    nameless = await create_player(dto.User(tg_id=109), dao)

    assert await renew_id_usernames(dao) == []
    assert (await check_dao.player.get_by_id(nameless.id)).username == f"id{nameless.id}"
