from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel, OAuthFlowPassword
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from starlette.responses import Response

from shvatka.api.app.config.models.auth import AuthConfig
from shvatka.api.auth.responses import Token


class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(
        self,
        token_url: str,
        cookie_name: str = "Authorization",
        scheme_name: str | None = None,
        auto_error: bool = True,
    ) -> None:
        flows = OAuthFlowsModel(password=OAuthFlowPassword(tokenUrl=token_url))
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)
        self.cookie_name = cookie_name

    def get_token(self, request: Request) -> Token:
        authorization = request.cookies.get(self.cookie_name, "")

        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return Token(access_token=param, token_type="bearer")  # noqa: S106


def set_auth_response(config: AuthConfig, response: Response, token: Token) -> None:
    response.set_cookie(
        config.cookie_name,
        value=f"{token.token_type} {token.access_token}",
        samesite=config.samesite,
        domain=config.cookie_domain,
        httponly=config.httponly,
        secure=config.secure,
        max_age=int(config.token_expire.total_seconds()),
    )


def delete_auth_response(config: AuthConfig, response: Response) -> None:
    # the attributes have to repeat the ones the cookie was set with,
    # otherwise the browser keeps the cookie and deletes nothing
    response.delete_cookie(
        config.cookie_name,
        samesite=config.samesite,
        domain=config.cookie_domain,
        httponly=config.httponly,
        secure=config.secure,
    )
