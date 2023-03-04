import asyncio

from aiohttp import ClientSession, MultipartWriter

from src.infrastructure.crawler.auth import get_auth_cookie
from src.infrastructure.crawler.constants import BASE_URL
from src.infrastructure.crawler.models import (
    LevelPuzzle,
    Hint,
    GameForUpload,
)


async def upload(game: GameForUpload):
    async with ClientSession(cookies=await get_auth_cookie()) as session:
        await remove_all_scn(session)
        for level in game:
            await asyncio.sleep(1)
            await add_level_puzzle(session, level.puzzle)
            for hint in level.hints:
                await asyncio.sleep(1)
                await add_hint(session, hint)


async def remove_all_scn(session: ClientSession):
    async with session.post(
        BASE_URL,
        data={"act": "module", "module": "reps", "cmd": "scn", "delg": "1"},
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
        BASE_URL,
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
        BASE_URL,
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
