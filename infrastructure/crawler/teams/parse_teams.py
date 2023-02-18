import asyncio
import typing
from datetime import date, datetime
from urllib.parse import urlparse, parse_qs

from aiohttp import ClientSession
from lxml import etree

from infrastructure.crawler.auth import get_auth_cookie
from infrastructure.crawler.constants import TEAMS_URL
from infrastructure.crawler.models.team import Player, Team


async def get_all_teams():
    async with ClientSession(cookies=await get_auth_cookie()) as session:
        teams_html_text = await download_teams(session)
        teams = await TeamsParser(teams_html_text, session=session).build()
    for team in teams:
        print(team)


async def download_teams(session: ClientSession) -> str:
    async with session.get(TEAMS_URL, allow_redirects=False) as resp:
        resp.raise_for_status()
        return await resp.text(encoding="cp1251", errors="backslashreplace")


class TeamsParser:
    def __init__(self, html_str: str, *, session: ClientSession):
        self.html = etree.HTML(html_str, base_url="shvatka.ru")
        self.session = session
        self.teams = []

    async def parse_teams(self):
        for team_element in self.html.xpath('//table//td[@class="row2"]/b/a'):
            team_name = team_element.text
            url = team_element.get("href")
            games_element = team_element.xpath("../../../td[4]")[0]
            games = list(map(int, etree.tostring(games_element, method="text").decode("utf8").split()))
            team_id = int(parse_qs(typing.cast(str, urlparse(url).query))["id"][0])
            team = Team(
                name=team_name,
                id=team_id,
                url=url,
                games=games,
                players=await self.parse_team_players(url)
            )
            self.teams.append(team)

    async def parse_team_players(self, team_url: str) -> list[Player]:
        await asyncio.sleep(0.3)
        players = []
        async with self.session.get(team_url) as resp:
            resp.raise_for_status()
            players_html = etree.HTML(await resp.text(encoding="cp1251", errors="backslashreplace"), base_url="shvatka.ru")
        for player_element in players_html.xpath('//table//td[@class="row1"]/b/a'):
            url = player_element.get("href")
            name = player_element.text
            root = player_element.xpath("../../..")[0]
            role = root.xpath("td[2]")
            games = list(map(int, etree.tostring(root.xpath("td[3]")[0], method="text").decode("utf8").split()))
            player = Player(
                name=name,
                role=role,
                url=url,
                games=games,
                registered_at=await self.parse_player_registered_date(url),
            )
            players.append(player)
        return players

    async def parse_player_registered_date(self, url: str) -> date:
        await asyncio.sleep(0.3)
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            player = etree.HTML(await resp.text(encoding="cp1251", errors="backslashreplace"), base_url="shvatka.ru")
        date_ = player.xpath("//div[@class='postdetails']/br")[0].tail.strip().removeprefix("Регистрация:").strip()
        return datetime.strptime(date_, "%d. %m. %y")

    async def build(self) -> list[Team]:
        await self.parse_teams()
        return self.teams


if __name__ == '__main__':
    asyncio.run(get_all_teams())
