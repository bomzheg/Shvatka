import logging
import typing
import uuid
from datetime import datetime, timedelta
from io import BytesIO
from typing import BinaryIO

from aiohttp import (
    ClientSession,
    ClientConnectorError,
    ClientResponseError,
    ServerDisconnectedError,
    ClientOSError,
)
from lxml import etree
from lxml.etree import _Element

from shvatka.core.models import enums
from shvatka.core.models.dto import scn
from shvatka.core.utils.datetime_utils import tz_utc, tz_game, add_timezone
from shvatka.infrastructure.crawler.constants import GAME_URL_TEMPLATE
from shvatka.infrastructure.crawler.game_scn.parser.parser import (
    ContentDownloadError,
    PARSER_ERROR_IMG,
    EVENING_TIME,
)
from shvatka.infrastructure.crawler.models.stat import LevelTime, Key, GameStat

logger = logging.getLogger(__name__)


async def download(game_id: int, session: ClientSession) -> str:
    async with session.get(
        GAME_URL_TEMPLATE.format(game_id=game_id), allow_redirects=False
    ) as resp:
        return await resp.text(encoding="cp1251", errors="backslashreplace")


class SvastEngineGameParser:
    def __init__(
        self, html_str: str, id_: int, name: str, start_at: datetime, *, session: ClientSession
    ):
        self.html = etree.HTML(html_str, base_url="shvatka.ru")
        self.session = session
        self.id: int = id_
        self.name: str = name
        self.start_at: datetime = start_at
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
        logger.info("parsing game %s ...", self.id)

    async def parse_scenario(self) -> None:  # noqa: C901
        (scn_element,) = self.html.xpath(
            "//div[@class='spoiler-block' and a[contains(text(), 'Сценарий')]]"
            "/div[@class='spoiler-content']"
        )
        for element in scn_element.xpath("./*"):
            if element.tag == "center":
                if element.xpath("./center/h2"):
                    #  main caption "Сценарий"
                    continue
            if element.tag == "strong":
                caption = element.xpath("./center/font")
                if caption and caption[0].text:
                    prompt: tuple[str, ...] = caption[0].text.split()
                    if prompt[0] == "Уровень: " and prompt[1].isnumeric():
                        self.level_number = int(prompt[1].strip("."))
                        continue
            if element.tag == "p":
                if hint_caption_container := element.xpath("./strong"):
                    if (
                        hint_caption_container.text
                        and len(hint_caption_container.text.split()) == 2
                    ):
                        hint_caption, number = hint_caption_container.text.split()  # type: str
                        if hint_caption == "Подсказка":
                            time, minutes_caption = element.text.split()  # type: str
                            if minutes_caption == "мин.)":
                                self.build_time_hint()
                                time = time.removeprefix("(")
                                self.time = int(time or -1)
                                continue
            if iframe_tags := element.xpath("descendant-or-self::iframe"):
                for iframe in iframe_tags:
                    self.current_hint_parts.append(iframe.get("src"))
            if img_tags := element.xpath("descendant-or-self::img"):
                for img in img_tags:
                    self.build_current_hint()
                    guid = str(uuid.uuid4())
                    try:
                        self.files[guid] = await self.download_content(img.get("src"))
                        self.hints.append(scn.PhotoHint(file_guid=guid))
                    except ContentDownloadError:
                        self.files[guid] = BytesIO(PARSER_ERROR_IMG)
                        self.hints.append(
                            scn.PhotoHint(
                                file_guid=guid,
                                caption=f"не удалось скачать контент "
                                f"по ссылке {img.get('src')}",
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
        rows = self.html.xpath("//table/tbody[tr[td[text() = 'Название команды']]]/tr")
        results: dict[str, list[LevelTime]] = {}
        for row in rows[1:]:
            cells = row.xpath("./td")
            team_name = typing.cast(str, cells[0].text)
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
            time = datetime.strptime(cell.text, "%H:%M:%S").time()
        except ValueError:
            return None
        if time < EVENING_TIME:
            td = timedelta(days=1)
        else:
            td = timedelta(seconds=0)
        at = datetime.combine(date=self.start_at.date() + td, time=time, tzinfo=tz_game)
        return at

    def parse_keys(self) -> dict[str, list[Key]]:
        tables = self.html.xpath(
            "//div[@class='spoiler-block' and a[contains(text(), 'Логи')]]"
            "/div[@class='spoiler-content']//tbody"
        )
        log_keys: dict[str, list[Key]] = {}
        for table in tables:
            rows = table.xpath(".//tr")
            team_name = rows[0].xpath("../../preceding-sibling::p")[0].text
            keys: list[Key] = []
            keys_buffer: list[Key] = []
            level = 1
            for row in rows[1:]:
                cells = row.xpath("./td")
                assert isinstance(cells, list)
                try:
                    time_element, key_element = cells  # type: _Element
                except ValueError as e:
                    logger.error(
                        "can't parse key log for cells %s",
                        [cell.text for cell in cells],
                        exc_info=e,
                    )
                    continue
                local_date = datetime.strptime(time_element.text, "%Y-%m-%d %H:%M:%S")
                keys_buffer.append(
                    Key(
                        player=None,
                        value=key_element.text,
                        at=add_timezone(local_date).astimezone(tz_utc),
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
            keys={typing.cast(scn.TextHint, self.time_hints[-1].hint).text},
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


def get_finished_level_number(cells: list[_Element]):
    return int(cells[0].text.strip().removeprefix("Уровень").removesuffix("закончен").strip())


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
