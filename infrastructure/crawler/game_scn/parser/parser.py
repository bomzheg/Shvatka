from datetime import datetime
from pprint import pprint

from aiohttp import ClientSession
from lxml import etree

from infrastructure.crawler.auth import get_auth_cookie
from infrastructure.crawler.constants import GAME_URL_TEMPLATE, GAMES_URL
from shvatka.models import dto
from shvatka.models.dto.scn import LevelScenario, TimeHint, TextHint, BaseHint
from shvatka.models.dto.scn.game import ParsedCompletedGameScenario


async def get_all_games():
    games = []
    async with ClientSession(cookies=await get_auth_cookie()) as session:
        for game_id in reversed(await get_games_ids(session)):
            html_text = await download(game_id, session)
            with open("131.html", "w", encoding="utf8") as f:
                f.write(html_text)
            games.append(GameParser(html_text).build())
    return games


async def get_games_ids(session: ClientSession) -> list[int]:
    async with session.get(GAMES_URL) as resp:
        return list(range(132))


async def download(game_id: int, session: ClientSession) -> str:
    async with session.get(GAME_URL_TEMPLATE.format(game_id=game_id)) as resp:
        return await resp.text(encoding="cp1251")


class GameParser:
    def __init__(self, html_str: str):
        self.html = etree.HTML(html_str, base_url="shvatka.ru")
        self.id: int = 0
        self.name: str = ""
        self.start_at: datetime | None = None
        self.current_hint_parts: list[str] = []
        self.levels: list[LevelScenario] = []
        self.hints: list[BaseHint] = []
        self.time_hints: list[TimeHint] = []
        self.level_number = 0
        self.keys: set[str] = set()
        self.time: int = 0

    def parse_game_head(self):
        self.id = int(self.html.xpath("//div[@class='maintitle']/b")[0].text)
        self.name = self.html.xpath("//div[@class='maintitle']/b/a")[0].text
        started_at_text = self.html.xpath("//div[@class='maintitle']/b/span[@id='dt']")[0].text
        self.start_at = datetime.strptime(started_at_text, "%d.%m.%y в %H:%M")

    def parse_scenario(self):
        scn_element, = self.html.xpath("//div[@id='sc']//div[@class='borderwrap']//tr[@class='ipbtable']/td")
        for element in scn_element.xpath("./*"):
            if element.tag == "center":
                if self.keys:
                    self.build_level()
                self.keys = {b.tail for b in element.xpath("./b")}
                self.level_number = int(element.xpath("./b")[0].text.split()[1].strip("."))
            elif element.tag == "b":
                self.build_time_hint()
                hint_caption, number, time, minutes_caption = element.text.split()
                assert hint_caption == "Подсказка"
                assert minutes_caption == "мин.)"
                time = time.removeprefix("(")
                self.time = int(time or -1)
            else:
                if img := element.xpath(".//img"):
                    self.build_current_hint()
                    self.hints.append(TextHint(text=img[0].get("src")))
                if element.text:
                    self.current_hint_parts.append(element.text)
                if element.tail:
                    self.current_hint_parts.append(element.tail)
        self.build_level()

    def build_current_hint(self):
        if not self.current_hint_parts:
            return
        self.hints.append(TextHint(text="\n".join(self.current_hint_parts)))
        self.current_hint_parts = []

    def build_time_hint(self):
        self.build_current_hint()
        self.time_hints.append(
            TimeHint(time=self.time, hint=[
                *self.hints,
            ])
        )
        self.hints = []

    def build_level(self):
        self.build_time_hint()
        level = LevelScenario(
            id=f"game_{self.id}:lvl_{self.level_number}",
            time_hints=self.time_hints,
            keys=self.keys,
        )
        self.levels.append(level)
        self.time_hints = []
        self.keys = set()
        self.time = 0
        self.level_number = 0

    def build(self) -> dto.Game:
        self.parse_game_head()
        self.parse_scenario()
        game = ParsedCompletedGameScenario(
            id=self.id,
            name=self.name,
            start_at=self.start_at,
            levels=self.levels,
            files=[],
        )
        return game


if __name__ == '__main__':
    with open("131.html", encoding="utf8") as f:
        text = f.read()
    pprint(GameParser(text).build())
