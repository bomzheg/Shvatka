from datetime import datetime
from pprint import pprint

from aiohttp import ClientSession
from lxml import etree

from infrastructure.crawler.auth import get_auth_cookie
from infrastructure.crawler.constants import GAME_URL_TEMPLATE, GAMES_URL
from shvatka.models import dto
from shvatka.models.dto.scn import LevelScenario, TimeHint, TextHint
from shvatka.models.enums import GameStatus


async def get_all_games():
    games = []
    async with ClientSession(cookies=await get_auth_cookie()) as session:
        for game_id in reversed(await get_games_ids(session)):
            html_text = await download(game_id, session)
            with open("131.html", "w", encoding="utf8") as f:
                f.write(html_text)
            games.append(parse(html_text))
    return games


async def get_games_ids(session: ClientSession) -> list[int]:
    async with session.get(GAMES_URL) as resp:
        return list(range(132))


async def download(game_id: int, session: ClientSession) -> str:
    async with session.get(GAME_URL_TEMPLATE.format(game_id=game_id)) as resp:
        return await resp.text(encoding="cp1251")


def parse(html_str: str) -> dto.Game:
    html = etree.HTML(html_str, base_url="shvatka.ru")
    id_ = html.xpath("//div[@class='maintitle']/b")[0].text
    name = html.xpath("//div[@class='maintitle']/b/a")[0].text
    started_at_text = html.xpath("//div[@class='maintitle']/b/span[@id='dt']")[0].text
    print(id_, name, started_at_text)
    scn_element, = html.xpath("//div[@id='sc']//div[@class='borderwrap']//tr[@class='ipbtable']/td")
    current_hint = []
    levels = []
    hints = []
    keys = {}
    time = 0
    for element in scn_element.xpath("./*"):
        if element.tag == "center":
            if keys:
                hints.append(TimeHint(time=time, hint=[TextHint(text="\n".join(current_hint))]))
                time = 0
                level = LevelScenario(id="", time_hints=hints, keys=keys)
                levels.append(level)
                hints = []
            keys = {b.tail for b in element.xpath("./b")}
        elif element.tag == "b":
            hints.append(TimeHint(time=time, hint=[TextHint(text="\n".join(current_hint))]))
            hint_caption, number, time, minutes_caption = element.text.split()
            assert hint_caption == "Подсказка"
            assert minutes_caption == "мин.)"
            time = time.removeprefix("(")
            time = int(time or -1)
            current_hint = []
        else:
            if element.text:
                current_hint.append(element.text)
            if element.tail:
                current_hint.append(element.tail)

    hints.append(TimeHint(time=time, hint=[TextHint(text="\n".join(current_hint))]))
    level = LevelScenario(id="", time_hints=hints, keys=keys)
    levels.append(level)
    game = dto.FullGame(
        id=id_,
        name=name,
        start_at=datetime.strptime(started_at_text, "%d.%m.%y в %H:%M"),
        author=None,
        status=GameStatus.complete,
        manage_token="",
        published_channel_id=None,
        levels=levels,
    )
    return game


if __name__ == '__main__':
    with open("131.html", encoding="utf8") as f:
        text = f.read()
    pprint(parse(text))
