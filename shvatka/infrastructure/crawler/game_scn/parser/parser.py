import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from aiohttp import (
    ClientSession,
    ClientConnectorError,
    ClientResponseError,
    ServerDisconnectedError,
    ClientOSError,
)
from dataclass_factory import Factory, Schema, NameStyle
from lxml import etree
from lxml.etree import _Element

from shvatka.core.models import enums
from shvatka.core.models.dto import scn
from shvatka.core.services.scenario.scn_zip import pack_scn
from shvatka.core.utils.datetime_utils import tz_local, tz_utc
from shvatka.infrastructure.crawler.auth import get_auth_cookie
from shvatka.infrastructure.crawler.constants import GAME_URL_TEMPLATE
from shvatka.infrastructure.crawler.game_scn.parser.resourses import load_error_img
from shvatka.infrastructure.crawler.models.stat import LevelTime, Key, GameStat

logger = logging.getLogger(__name__)
EVENING_TIME = datetime.strptime("20:00:00", "%H:%M:%S").time()
PARSER_ERROR_IMG = load_error_img()


class ContentDownloadError(IOError):
    pass


async def get_all_games(games_ids: list[int]) -> list[scn.ParsedCompletedGameScenario]:
    games = []
    async with ClientSession(cookies=await get_auth_cookie()) as session:
        for game_id in reversed(games_ids):
            await asyncio.sleep(1)
            html_text = await download(game_id, session)
            try:
                games.append(await GameParser(html_text, session=session).build())
            except (ValueError, AttributeError) as e:
                logger.error("can't parse game %s", game_id, exc_info=e)
    return games


async def download(game_id: int, session: ClientSession) -> str:
    async with session.get(
        GAME_URL_TEMPLATE.format(game_id=game_id), allow_redirects=False
    ) as resp:
        return await resp.text(encoding="cp1251", errors="backslashreplace")


class GameParser:
    def __init__(self, html_str: str, *, session: ClientSession):
        self.html = etree.HTML(html_str, base_url="shvatka.ru")
        self.session = session
        self.id: int = 0
        self.name: str = ""
        self.start_at: datetime | None = None
        self.current_hint_parts: list[str] = []
        self.levels: list[scn.LevelScenario] = []
        self.hints: list[scn.BaseHint] = []
        self.time_hints: list[scn.TimeHint] = []
        self.level_number = 0
        self.keys: set[str] = set()
        self.time: int = 0
        self.files: dict[str, BinaryIO] = {}
        self.files_meta: list[scn.FileMetaLightweight] = []

    def parse_game_head(self):
        self.id = int(self.html.xpath("//div[@class='maintitle']/b")[0].text)
        logger.info("parsing game %s ...", self.id)
        self.name = self.html.xpath("//div[@class='maintitle']/b/a")[0].text
        started_at_text = self.html.xpath("//div[@class='maintitle']/b/span[@id='dt']")[0].text
        self.start_at = datetime.strptime(started_at_text, "%d.%m.%y в %H:%M")

    async def parse_scenario(self):  # noqa: C901
        (scn_element,) = self.html.xpath(
            "//div[@id='sc']//div[@class='borderwrap']//tr[@class='ipbtable']/td"
        )
        for element in scn_element.xpath("./*"):
            if element.tag == "center":
                caption = element.xpath("./b")
                if caption and caption[0].text:
                    prompt: tuple[str, ...] = caption[0].text.split()
                    if (
                        prompt[0] == "Уровень"
                        and prompt[1].strip(".").isnumeric()
                        and prompt[2] == "Ключ:"
                    ):
                        if self.keys:  # if not - it's first level
                            self.build_level()
                        self.keys = {b.tail for b in element.xpath("./b")}
                        self.level_number = int(prompt[1].strip("."))
                        continue
            if element.tag == "b":
                if element.text and len(element.text.split()) == 4:
                    hint_caption, number, time, minutes_caption = element.text.split()  # type: str
                    if hint_caption == "Подсказка" and minutes_caption == "мин.)":
                        self.build_time_hint()
                        time = time.removeprefix("(")
                        self.time = int(time or -1)
                        continue
            if iframe_tags := element.xpath("descendant-or-self::iframe"):
                for iframe in iframe_tags:
                    self.current_hint_parts.append(iframe.get("shvatka"))
            if img_tags := element.xpath("descendant-or-self::img"):
                for img in img_tags:
                    self.build_current_hint()
                    guid = str(uuid.uuid4())
                    try:
                        self.files[guid] = await self.download_content(img.get("shvatka"))
                        self.hints.append(scn.PhotoHint(file_guid=guid))
                    except ContentDownloadError:
                        self.files[guid] = BytesIO(PARSER_ERROR_IMG)
                        self.hints.append(
                            scn.PhotoHint(
                                file_guid=guid,
                                caption=f"не удалось скачать контент "
                                f"по ссылке {img.get('shvatka')}",
                            )
                        )
                    self.files_meta.append(
                        scn.FileMetaLightweight(
                            guid=guid,
                            original_filename=guid,
                            extension=".jpg",
                            content_type=enums.HintType.photo,
                        )
                    )
            if element.text:
                self.current_hint_parts.append(element.text)
            if element.tail:
                self.current_hint_parts.append(element.tail)
        self.build_level()

    def parse_results(self) -> dict[str, list[LevelTime]]:
        rows = self.html.xpath("//div[@id='tb']//tr[@class='ipbtable']")
        results = {}
        for row in rows:
            cells = row.xpath("./td")
            team_name = cells[0].xpath("./b")[0].text
            level_times = []
            for level_number, cell in enumerate(cells[1:], 1):
                try:
                    at = self.get_result_datetime(cell)
                except IndexError as e:
                    logger.error("can't parse results", exc_info=e)
                    break
                level_times.append(
                    LevelTime(number=level_number, at=at.astimezone(tz_utc) if at else None)
                )
            results[team_name] = level_times
        return results

    def get_result_datetime(self, cell: _Element) -> datetime | None:
        try:
            time = datetime.strptime(cell.text or cell.xpath("./font")[0].text, "%H:%M:%S").time()
        except ValueError:
            return None
        if time < EVENING_TIME:
            td = timedelta(days=1)
        else:
            td = timedelta(seconds=0)
        at = datetime.combine(date=self.start_at.date() + td, time=time, tzinfo=tz_local)
        return at

    def parse_keys(self) -> dict[str, list[Key]]:
        tables = self.html.xpath("//div[@id='logs']//table")
        log_keys = {}
        for table in tables:
            rows = table.xpath(".//tr")
            team_name = rows[0].xpath("./td")[0].text
            keys = []
            keys_buffer = []
            level = 1
            for row in rows[2:]:
                cells = row.xpath("./td")
                if len(cells) == 1:
                    if get_finished_level_number(cells) == level - 1:
                        # Sometimes (game 60) it may contain
                        # two times level x completed ("Уровень 1 завершён")
                        for key in keys_buffer:
                            key.level -= 1
                    else:
                        level += 1
                    keys.extend(keys_buffer)
                    keys_buffer.clear()
                    continue
                try:
                    time, key, player = cells
                except ValueError as e:
                    logger.error(
                        "can't parse key log for cells %s",
                        [cell.text for cell in cells],
                        exc_info=e,
                    )
                    continue
                local_date = datetime.strptime(time.text, "%Y-%m-%d %H:%M:%S")
                keys_buffer.append(
                    Key(
                        player=player.xpath("./b")[0].text,
                        value=key.text,
                        at=datetime.combine(
                            date=local_date.date(), time=local_date.time(), tzinfo=tz_local
                        ).astimezone(tz_utc),
                        level=level,
                    )
                )
            keys.extend(keys_buffer)
            keys_buffer.clear()
            log_keys[team_name] = keys
        return log_keys

    async def download_content(self, url: str) -> BinaryIO:
        try:
            async with self.session.get(url.strip()) as resp:
                resp.raise_for_status()
                if not resp.content_type.startswith("image"):
                    raise ValueError(
                        f"response contains no image, content-type is {resp.content_type}"
                    )
                return BytesIO(await resp.content.read())
        except (
            ClientConnectorError,
            ClientResponseError,
            ServerDisconnectedError,
            ClientOSError,
            ValueError,
        ) as e:
            logger.error("couldnt load content for url %s", url, exc_info=e)
            raise ContentDownloadError()

    def build_current_hint(self):
        parts = list(filter(lambda p: p, map(lambda p: p.strip(), self.current_hint_parts)))
        self.current_hint_parts = []
        if not parts:
            return
        self.hints.append(scn.TextHint(text="\n".join(parts)))

    def build_time_hint(self):
        self.build_current_hint()
        self.time_hints.append(
            scn.TimeHint(
                time=self.time,
                hint=[
                    *self.hints,
                ],
            )
        )
        self.hints = []

    def build_level(self):
        self.build_time_hint()
        level = scn.LevelScenario(
            id=f"game_{self.id}-lvl_{self.level_number}",
            time_hints=self.time_hints,
            keys=self.keys,
        )
        self.levels.append(level)
        logger.debug("for game %s parsed level %s", self.id, self.level_number)
        self.time_hints = []
        self.keys = set()
        self.time = 0
        self.level_number = 0

    async def build(self) -> scn.ParsedCompletedGameScenario:
        self.parse_game_head()
        await self.parse_scenario()
        game = scn.ParsedCompletedGameScenario(
            id=self.id,
            name=self.name,
            start_at=self.start_at,
            levels=self.levels,
            files_contents=self.files,
            files=self.files_meta,
            stat=GameStat(
                results=self.parse_results(),
                keys=self.parse_keys(),
                id=self.id,
                start_at=self.start_at,
            ),
        )
        return game


async def save_all_scns_to_files(game_ids: list[int]):
    games = await get_all_games(game_ids)
    dcf = Factory(default_schema=Schema(name_style=NameStyle.kebab))
    path = Path() / "scn"
    path.mkdir(exist_ok=True)
    for game in games:
        dct = dcf.dump(game, scn.ParsedGameScenario)
        stat = BytesIO(
            json.dumps(dcf.dump(game.stat), ensure_ascii=False, indent=2).encode("utf-8")
        )
        stat.seek(0)
        scenario = scn.RawGameScenario(
            scn=dct, files={**game.files_contents, "results.json": stat}
        )
        packed_scenario = pack_scn(scenario)
        with open(path / f"{game.id}.zip", "wb") as f:
            logger.debug("saved to filename %s", f.name)
            f.write(packed_scenario.read())


def get_finished_level_number(cells: list[_Element]):
    return int(cells[0].text.strip().removeprefix("Уровень").removesuffix("закончен").strip())


def get_parseable_games_ids():
    unparseable_games_ids = {*range(19), 31, 51, 52, 84}
    """
    до 19 - игры публиковались, просто выкладывались на форуме
    31 - Ночной детектив (не стандарт)
    51 - не была проведена до конца
    52, 84 - Тачки и Гарри Поттер - нестандартный движок
    """
    all_games_ids = set(range(132))
    return list(sorted(all_games_ids - unparseable_games_ids))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(save_all_scns_to_files(get_parseable_games_ids()))
