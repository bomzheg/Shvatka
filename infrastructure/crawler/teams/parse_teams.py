from aiohttp import ClientSession
from lxml import etree

from infrastructure.crawler.auth import get_auth_cookie
from infrastructure.crawler.constants import TEAMS_URL


async def get_all_teams():
    async with ClientSession(cookies=await get_auth_cookie()) as session:
        teams_html_text = await download_teams(session)


async def download_teams(session: ClientSession) -> str:
    async with session.get(TEAMS_URL, allow_redirects=False) as resp:
        return await resp.text(encoding="cp1251", errors="backslashreplace")


class TeamParser:
    def __init__(self, html_str: str, *, session: ClientSession):
        self.html = etree.HTML(html_str, base_url="shvatka.ru")
        self.session = session
        self.teams = []
