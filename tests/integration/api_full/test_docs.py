import pytest
from httpx import AsyncClient

from shvatka.core.utils.doc_pages import DocPage


@pytest.mark.asyncio
async def test_doc_pages_are_listed_for_the_ui(client: AsyncClient):
    resp = await client.get("/docs/pages")
    assert resp.is_success
    pages = resp.json()["pages"]
    assert {page.name for page in DocPage} == set(pages)


@pytest.mark.asyncio
async def test_a_page_carries_its_url_and_title(client: AsyncClient):
    resp = await client.get("/docs/pages")
    create_team = resp.json()["pages"][DocPage.CREATE_TEAM.name]
    # the test config publishes the docs of 3.7.0 on its own domain
    assert (
        create_team["url"]
        == "https://docs.shvatka-test.bomzheg.dev/shvatka/3.7.0/setup_team/create_team.html"
    )
    assert DocPage.CREATE_TEAM.nav_title == create_team["title"]


@pytest.mark.asyncio
async def test_the_pages_need_no_authentication(client: AsyncClient):
    """The ui asks for them before anybody has logged in."""
    resp = await client.get("/docs/pages")
    assert resp.status_code == 200
