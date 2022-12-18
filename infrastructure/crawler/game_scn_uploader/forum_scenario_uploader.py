import asyncio
import os

from aiohttp import ClientSession, MultipartWriter

from ..models import Credentials
from ..models import (
    LevelPuzzle, Hint, GameForUpload,
)

COOKIE_NAME = "shvatkasession_id"

admin = "http://www.shvatka.ru/index.php?act=module&module=reps&cmd=scn"
base_url = "http://www.shvatka.ru/index.php"


async def upload(game: GameForUpload):
    async with ClientSession() as session:
        creds = Credentials(
            username=os.getenv("SH_USERNAME"),
            password=os.getenv("SH_PASSWORD"),
        )
        cookies = await auth(session, creds)
    async with ClientSession(cookies=cookies) as session:
        await remove_all_scn(session)
        for level in game:
            await asyncio.sleep(1)
            await add_level_puzzle(session, level.puzzle)
            for hint in level.hints:
                await asyncio.sleep(1)
                await add_hint(session, hint)


async def auth(session: ClientSession, creds: Credentials):
    php_session = await get_login_page(session)
    cookies = await authorize(session, php_session, creds)
    cookies[COOKIE_NAME] = php_session
    return cookies


async def remove_all_scn(session: ClientSession):
    async with session.post(
        base_url,
        data={
            "act": "module",
            "module": "reps",
            "cmd": "scn",
            "delg": "1"
        },
    ) as resp:
        resp.raise_for_status()
        assert resp.ok


async def add_level_puzzle(session: ClientSession, hint: LevelPuzzle):
    data = {
        "act": "module",
        "module": "shedit",
        "cm": "3",
        "lev": str(hint.level_number),
        "npod": str(hint.hint_number),
        "execs": "1",
        "ptm": str(hint.next_hint_time),
        "keyw": preprocess_text(hint.key),
        "b_keyw": preprocess_text(hint.brain_key),
    }
    mp = write_multipart(data, hint.text)
    async with session.post(
        base_url,
        data=mp,

    ) as resp:
        resp.raise_for_status()
        assert resp.ok


async def add_hint(session: ClientSession, hint: Hint):
    data = {
        "act": "module",
        "module": "shedit",
        "cm": "3",
        "lev": str(hint.level_number),
        "npod": str(hint.hint_number),
        "execs": "1",
        "ptm": str(hint.next_hint_time),
    }
    mp = write_multipart(data, hint.text)
    async with session.post(
        base_url,
        data=mp,
    ) as resp:
        resp.raise_for_status()
        assert resp.ok


def write_multipart(data: dict[str, str], hint_text: str) -> MultipartWriter:
    with MultipartWriter("form-data") as mp:
        for key, value in data.items():
            part = mp.append(value)
            part.set_content_disposition("form-data", name=key)
        part = mp.append(preprocess_text(hint_text))
        part.set_content_disposition("form-data", name="textl")
    return mp


def preprocess_text(text: str):
    return text.encode("cp1251")


async def get_login_page(session: ClientSession):
    async with session.get(base_url, params=dict(act="Login", CODE="00")) as resp:
        resp.raise_for_status()
        assert resp.ok
        return resp.cookies[COOKIE_NAME].value


async def authorize(session: ClientSession, php_session: str, creds: Credentials):
    async with session.post(
        base_url,
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
        params=dict(s=php_session, act="Login", CODE="01")
    ) as resp:
        resp.raise_for_status()
        assert resp.ok
        cookies = resp.cookies
        return {
            "shvatkamember_id": cookies["shvatkamember_id"].value,
            "shvatkapass_hash": cookies["shvatkapass_hash"].value,
        }
