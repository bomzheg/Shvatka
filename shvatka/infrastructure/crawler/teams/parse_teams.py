import asyncio
import json
import logging
import typing
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from aiohttp import ClientSession
from dataclass_factory import Factory, Schema, NameStyle
from lxml import etree

from shvatka.common.config.parser.logging_config import setup_logging
from shvatka.infrastructure.crawler.auth import get_auth_cookie
from shvatka.infrastructure.crawler.constants import TEAMS_URL
from shvatka.infrastructure.crawler.factory import get_paths
from shvatka.infrastructure.crawler.models.team import ParsedPlayer, ParsedTeam

logger = logging.getLogger(__name__)


async def get_all_teams() -> list[ParsedTeam]:
    async with ClientSession(cookies=await get_auth_cookie()) as session:
        teams_html_text = await download_teams(session)
        teams = await TeamsParser(teams_html_text, session=session).build()
    return teams


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
            games = get_games_numbers(team_element.xpath("../../../td[4]")[0])
            team_id = int(parse_qs(typing.cast(str, urlparse(url).query))["id"][0])
            team = ParsedTeam(
                name=team_name,
                id=team_id,
                url=url,
                games=games,
                players=await self.parse_team_players(url),
            )
            logger.info("parsed team: %s", team.name)
            self.teams.append(team)

    async def parse_team_players(self, team_url: str) -> list[ParsedPlayer]:
        await asyncio.sleep(0.5)
        players = []
        async with self.session.get(team_url) as resp:
            resp.raise_for_status()
            players_html = etree.HTML(
                await resp.text(encoding="cp1251", errors="backslashreplace"),
                base_url="shvatka.ru",
            )
        for player_element in players_html.xpath('//table//td[@class="row1"]/b/a'):
            url = player_element.get("href")
            name = player_element.text
            root = player_element.xpath("../../..")[0]
            role = root.xpath("td[2]")[0].text
            games = get_games_numbers(root.xpath("td[4]")[0])
            player = ParsedPlayer(
                name=name,
                role=role,
                url=url,
                games=games,
                registered_at=await self.parse_player_registered_date(url),
                forum_id=int(parse_qs(typing.cast(str, urlparse(url).query))["showuser"][0]),
            )
            players.append(player)
        return players

    async def parse_player_registered_date(self, url: str) -> date:
        await asyncio.sleep(0.5)
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            player = etree.HTML(
                await resp.text(encoding="cp1251", errors="backslashreplace"),
                base_url="shvatka.ru",
            )
        date_ = (
            player.xpath("//div[@class='postdetails']/br")[0]
            .tail.strip()
            .removeprefix("Регистрация:")
            .strip()
        )
        return datetime.strptime(date_, "%d. %m. %y")

    async def build(self) -> list[ParsedTeam]:
        await self.parse_teams()
        return self.teams


def get_games_numbers(games_element) -> list[int]:
    return list(map(int, etree.tostring(games_element, method="text").decode("utf8").split()))


async def main_team_parser():
    paths = get_paths()
    setup_logging(paths)
    teams = await get_all_teams()
    dcf = Factory(default_schema=Schema(name_style=NameStyle.kebab))
    path = Path(__file__).parent
    with open(path / "teams.json", "w", encoding="utf8") as f:
        json.dump(dcf.dump(teams), f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    asyncio.run(main_team_parser())
