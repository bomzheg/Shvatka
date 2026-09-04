from shvatka.common.config.models.main import DocsConfig
from shvatka.common.docs import DocsUrlFactory
from shvatka.core.utils import exceptions
from shvatka.core.utils.doc_pages import DocPage


def factory(**kwargs) -> DocsUrlFactory:
    return DocsUrlFactory(DocsConfig(**kwargs))


def test_defaults_point_at_the_docs_of_master():
    assert (
        factory().get_page_url(DocPage.PLAY)
        == "https://bomzheg.github.io/Shvatka/shvatka/player/play.html"
    )


def test_domain_is_configurable():
    docs = factory(base_url="https://docs.example.org", version="4.0.0")
    assert (
        docs.get_page_url(DocPage.PLAY)
        == "https://docs.example.org/shvatka/4.0.0/player/play.html"
    )


def test_a_release_pins_its_own_tag():
    docs = factory(version="3.7.0")
    assert (
        docs.get_page_url(DocPage.PLAY)
        == "https://bomzheg.github.io/Shvatka/shvatka/3.7.0/player/play.html"
    )


def test_trailing_slash_does_not_double():
    docs = factory(base_url="https://docs.example.org/")
    assert docs.get_page_url(DocPage.PLAY) == "https://docs.example.org/shvatka/player/play.html"


def test_anchor_stays_after_the_extension():
    docs = factory(base_url="https://docs.example.org")
    assert (
        docs.get_page_url(DocPage.PLAY_KEYS)
        == "https://docs.example.org/shvatka/player/play.html#keys"
    )


def test_error_url():
    docs = factory(base_url="https://docs.example.org", version="3.7.0")
    url = docs.get_error_url(exceptions.InvalidKey())
    assert url == "https://docs.example.org/shvatka/3.7.0/player/play.html#keys"


def test_error_without_a_page_has_no_url():
    assert factory().get_error_url(exceptions.SHError()) is None
