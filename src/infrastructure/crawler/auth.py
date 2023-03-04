import os

from aiohttp import ClientSession

from src.infrastructure.crawler.constants import COOKIE_NAME, BASE_URL
from src.infrastructure.crawler.models import Credentials


async def auth(session: ClientSession, creds: Credentials):
    php_session = await get_login_page(session)
    cookies = await authorize(session, php_session, creds)
    cookies[COOKIE_NAME] = php_session
    return cookies


async def get_login_page(session: ClientSession):
    async with session.get(BASE_URL, params=dict(act="Login", CODE="00")) as resp:
        resp.raise_for_status()
        assert resp.ok
        return resp.cookies[COOKIE_NAME].value


async def authorize(session: ClientSession, php_session: str, creds: Credentials):
    async with session.post(
        BASE_URL,
        data={
            "CookieDate": "1",
            "act": "Login",
            "CODE": "01",
            "s": "",
            "referer": "",
            "UserName": creds.username,
            "PassWord": creds.password,
            "submit": "%C2%F5%EE%E4",
        },
        params=dict(s=php_session, act="Login", CODE="01"),
    ) as resp:
        resp.raise_for_status()
        assert resp.ok
        cookies = resp.cookies
        return {
            "shvatkamember_id": cookies["shvatkamember_id"].value,
            "shvatkapass_hash": cookies["shvatkapass_hash"].value,
        }


async def get_auth_cookie():
    async with ClientSession() as session:
        creds = Credentials(
            username=os.getenv("SH_USERNAME"),
            password=os.getenv("SH_PASSWORD"),
        )
        if not creds.username or not creds.password:
            raise EnvironmentError(
                "For run forum parsers, you have to specify next env variables: SH_USERNAME, SH_PASSWORD",
            )
        cookies = await auth(session, creds)
    return cookies
