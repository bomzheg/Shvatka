from pathlib import Path

import pytest

from shvatka.core.utils import exceptions
from shvatka.core.utils.doc_pages import DOC_PAGE_TITLES, DocPage

PAGES_ROOT = Path(__file__).resolve().parents[3] / "docs" / "modules" / "ROOT" / "pages"


@pytest.mark.parametrize("page", list(DocPage))
def test_every_page_exists_in_docs(page: DocPage):
    path, _, _ = page.value.partition("#")
    assert (PAGES_ROOT / f"{path}.adoc").is_file()


@pytest.mark.parametrize("page", [p for p in DocPage if "#" in p.value])
def test_every_anchor_is_declared_in_its_page(page: DocPage):
    path, _, anchor = page.value.partition("#")
    assert f"[#{anchor}]" in (PAGES_ROOT / f"{path}.adoc").read_text()


@pytest.mark.parametrize("page", list(DocPage))
def test_every_page_has_a_title(page: DocPage):
    assert page.nav_title
    assert page.nav_title == DOC_PAGE_TITLES[page]


def test_title_does_not_shadow_str_title():
    assert DocPage.PLAY.title() == "Player/Play"


def test_error_declares_its_page():
    assert exceptions.InvalidKey().doc_page == DocPage.PLAY_KEYS
    assert exceptions.WaiverForbidden().doc_page == DocPage.WAIVERS


def test_page_is_inherited():
    assert exceptions.PlayerAlreadyInTeam().doc_page == DocPage.JOIN_TEAM


def test_error_without_a_page():
    assert exceptions.SHError().doc_page is None


def test_page_can_be_given_at_the_raise_site():
    error = exceptions.PermissionsError(doc_page=DocPage.CHANGE_CAPTAIN)
    assert error.doc_page == DocPage.CHANGE_CAPTAIN


def test_given_page_overrides_the_class_one():
    error = exceptions.InvalidKey(doc_page=DocPage.LEVEL_CREATE)
    assert error.doc_page == DocPage.LEVEL_CREATE
