from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter

from shvatka.api.docs import responses
from shvatka.common.docs import DocsUrlFactory


@inject
async def get_doc_pages(docs: FromDishka[DocsUrlFactory]) -> responses.DocPages:
    """The pages the web ui links its own hints to.

    The engine owns where the documentation lives and what each page is called,
    so the ui asks instead of building urls itself — one place to fix when a
    page moves, and no docs configuration of its own.
    """
    return responses.DocPages.from_core(docs)


def setup() -> APIRouter:
    router = APIRouter(prefix="/docs", tags=["docs"])
    router.add_api_route("/pages", get_doc_pages, methods=["GET"])
    return router
