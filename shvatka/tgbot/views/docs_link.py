from aiogram.utils.text_decorations import html_decoration as hd

from shvatka.common.docs import DocsUrlFactory
from shvatka.core.utils.exceptions import SHError


def error_doc_link(error: SHError, docs: DocsUrlFactory) -> str | None:
    """An html link to the page explaining this error, when it has one."""
    url = docs.get_error_url(error)
    if url is None:
        return None
    assert error.doc_page is not None
    return f"ℹ️ Подробнее: {hd.link(hd.quote(error.doc_page.nav_title), url)}"
