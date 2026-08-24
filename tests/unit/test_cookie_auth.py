from datetime import timedelta
from typing import Literal

import pytest
from fastapi import HTTPException, Request
from starlette.responses import Response

from shvatka.api.app.config.models.auth import AuthConfig
from shvatka.api.app.utils.cookie_auth import (
    OAuth2PasswordBearerWithCookie,
    delete_auth_response,
    set_auth_response,
)
from shvatka.api.auth.responses import Token


def make_config(
    domain: str | None = None,
    cookie_name: str = "Authorization",
    samesite: Literal["lax", "strict", "none"] | None = "lax",
) -> AuthConfig:
    return AuthConfig(
        secret_key="secret",
        token_expire=timedelta(minutes=30),
        bot_username="shvatkatestbot",
        samesite=samesite,
        httponly=True,
        secure=True,
        auth_url="https://example.org/sh/login/data",
        bot_token="123:ABC",
        domain=domain,
        cookie_name=cookie_name,
    )


def set_cookie_header(config: AuthConfig) -> str:
    response = Response()
    set_auth_response(config, response, Token(access_token="token", token_type="bearer"))
    return response.headers["set-cookie"]


def make_request(cookie: str) -> Request:
    return Request(
        {
            "type": "http",
            "headers": [(b"cookie", cookie.encode())],
        }
    )


@pytest.mark.parametrize("domain", [None, ""], ids=["absent", "empty"])
def test_no_domain_means_host_only_cookie(domain: str | None):
    # a cookie without a Domain attribute goes back only to the host that set
    # it, so a sibling deployment can't overwrite it (issue #349)
    assert "Domain=" not in set_cookie_header(make_config(domain=domain))


def test_configured_domain_is_written():
    assert "Domain=bomzheg.dev" in set_cookie_header(make_config(domain="bomzheg.dev"))


def test_cookie_name_is_configurable():
    header = set_cookie_header(make_config(cookie_name="AuthorizationTest"))
    assert header.startswith("AuthorizationTest=")


def test_deleted_cookie_repeats_the_attributes_it_was_set_with():
    config = make_config(domain="bomzheg.dev", cookie_name="AuthorizationTest")
    response = Response()
    delete_auth_response(config, response)
    header = response.headers["set-cookie"]

    assert header.startswith('AuthorizationTest=""')
    assert "Domain=bomzheg.dev" in header
    assert "Max-Age=0" in header


def test_token_is_read_from_the_configured_cookie():
    cookie_auth = OAuth2PasswordBearerWithCookie(
        token_url="auth/token", cookie_name="AuthorizationTest"
    )

    token = cookie_auth.get_token(make_request("AuthorizationTest=bearer some-token"))

    assert Token(access_token="some-token", token_type="bearer") == token


def test_another_deployments_cookie_is_not_accepted():
    cookie_auth = OAuth2PasswordBearerWithCookie(
        token_url="auth/token", cookie_name="AuthorizationTest"
    )

    with pytest.raises(HTTPException):
        cookie_auth.get_token(make_request("Authorization=bearer some-token"))
