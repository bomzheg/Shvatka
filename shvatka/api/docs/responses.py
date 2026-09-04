from collections.abc import Mapping
from dataclasses import dataclass

from shvatka.common.docs import DocsUrlFactory
from shvatka.core.utils.doc_pages import DocPage


@dataclass(kw_only=True, frozen=True, slots=True)
class DocPageLink:
    url: str
    title: str

    @classmethod
    def from_core(cls, page: DocPage, docs: DocsUrlFactory) -> "DocPageLink":
        return cls(url=docs.get_page_url(page), title=page.nav_title)


@dataclass(kw_only=True, frozen=True, slots=True)
class DocPages:
    pages: Mapping[str, DocPageLink]

    @classmethod
    def from_core(cls, docs: DocsUrlFactory) -> "DocPages":
        return cls(pages={page.name: DocPageLink.from_core(page, docs) for page in DocPage})
