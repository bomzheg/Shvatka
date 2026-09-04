from shvatka.api.docs.responses import DocPages
from shvatka.common.config.models.main import DocsConfig
from shvatka.common.docs import DocsUrlFactory
from shvatka.core.utils.doc_pages import DocPage

DOCS = DocsUrlFactory(DocsConfig(base_url="https://docs.example.org", version="3.7.0"))


def test_every_page_is_offered_to_the_ui():
    assert {page.name for page in DocPage} == set(DocPages.from_core(DOCS).pages)


def test_a_page_is_keyed_by_its_name_not_its_path():
    pages = DocPages.from_core(DOCS).pages
    create_team = pages[DocPage.CREATE_TEAM.name]
    assert create_team.url == "https://docs.example.org/shvatka/3.7.0/setup_team/create_team.html"
    assert create_team.title == "Создание команды"
