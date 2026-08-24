import json
import typing

from starlette.requests import Request

from shvatka.api.app.error_handler import sh_exception_handler
from shvatka.common.config.models.main import DocsConfig
from shvatka.common.docs import DocsUrlFactory
from shvatka.core.utils import exceptions

DOCS = DocsUrlFactory(DocsConfig(base_url="https://docs.example.org", version="3.7.0"))


def request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/games",
            "headers": [],
            "query_string": b"",
        }
    )


def body(error: exceptions.SHError) -> dict[str, typing.Any]:
    response = sh_exception_handler(request(), error, docs=DOCS)
    return json.loads(response.body)


def test_error_body_carries_the_doc_url():
    content = body(exceptions.InvalidKey())
    assert "https://docs.example.org/shvatka/3.7.0/player/play.html#keys" == content["docUrl"]


def test_error_without_a_page_has_no_url():
    assert body(exceptions.SHError())["docUrl"] is None


def test_the_rest_of_the_body_is_untouched():
    content = body(exceptions.InvalidKey(text="wrong key"))
    assert "InvalidKey" == content["type"]
    assert "wrong key" == content["text"]
    assert exceptions.InvalidKey.notify_user == content["description"]
