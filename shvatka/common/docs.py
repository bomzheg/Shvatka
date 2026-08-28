from shvatka.common.config.models.main import DocsConfig
from shvatka.core.utils.doc_pages import DocPage
from shvatka.core.utils.exceptions import SHError


class DocsUrlFactory:
    """Builds links into the published user documentation.

    A ``DocPage`` names a page; where that page is published is deployment
    knowledge, so it lives in ``DocsConfig`` and reaches the edges through this
    factory. Core code (an exception, a view text) only ever names the page.
    """

    def __init__(self, config: DocsConfig) -> None:
        self.config = config

    def get_page_url(self, page: DocPage) -> str:
        path, _, anchor = page.value.partition("#")
        segments = [self.config.base_url.rstrip("/"), self.config.component]
        if self.config.version:
            segments.append(self.config.version)
        url = f"{'/'.join(segments)}/{path}.html"
        return f"{url}#{anchor}" if anchor else url

    def get_error_url(self, error: SHError) -> str | None:
        """The page explaining this error, if it has one."""
        if error.doc_page is None:
            return None
        return self.get_page_url(error.doc_page)
