import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from aiogram import Bot
from aiogram import html as hd
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest

from shvatka.core.season import dto
from shvatka.core.season.rules import SlotDigest
from shvatka.core.views.season import Announcement, SeasonAnnouncer
from shvatka.tgbot.services.bot_rights import BotRights

logger = logging.getLogger(__name__)

SLOT_DATE_FORMAT = r"%d.%m"

FREE = "🟢"
TAKEN = "🔒"
LINKED = "🎮"


@dataclass
class BotSeasonAnnouncer(SeasonAnnouncer):
    """The schedule as one pinned message in the game-log channel."""

    bot: Bot
    rights: BotRights
    log_chat_id: int

    async def publish(self, season: dto.Season) -> Announcement | None:
        message = await self.bot.send_message(chat_id=self.log_chat_id, text=render_season(season))
        await self._pin(message.message_id)
        return Announcement(chat_id=self.log_chat_id, message_id=message.message_id)

    async def update(self, season: dto.Season) -> None:
        if season.log_chat_id is None or season.log_message_id is None:
            # nothing was announced (no rights, or telegram refused): nothing to edit
            return
        try:
            await self.bot.edit_message_text(
                chat_id=season.log_chat_id,
                message_id=season.log_message_id,
                text=render_season(season),
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
            logger.debug("schedule of %s is already up to date", season.year)

    async def announce_digest(self, season: dto.Season, digests: Sequence[SlotDigest]) -> None:
        await self.bot.send_message(
            chat_id=season.log_chat_id or self.log_chat_id,
            text=render_digest(season, digests),
        )

    async def close(self, season: dto.Season) -> None:
        if season.log_chat_id is None or season.log_message_id is None:
            return
        if not await self.rights.can_pin(season.log_chat_id):
            logger.info("bot can't unpin messages in chat %s", season.log_chat_id)
            return
        try:
            await self.bot.unpin_chat_message(
                chat_id=season.log_chat_id, message_id=season.log_message_id
            )
        except TelegramAPIError as e:
            logger.warning("can't unpin the schedule of %s", season.year, exc_info=e)

    async def _pin(self, message_id: int) -> None:
        if not await self.rights.can_pin(self.log_chat_id):
            logger.info("bot can't pin messages in chat %s", self.log_chat_id)
            return
        try:
            await self.bot.pin_chat_message(chat_id=self.log_chat_id, message_id=message_id)
        except TelegramAPIError as e:
            logger.warning("can't pin the schedule message %s", message_id, exc_info=e)


def render_season(season: dto.Season) -> str:
    lines = [hd.bold(f"Расписание сезона {season.year}"), ""]
    lines.extend(render_slot(slot) for slot in sorted(season.slots, key=lambda s: s.date))
    return "\n".join(lines)


def render_slot(slot: dto.Slot) -> str:
    day = _day(slot.date)
    if slot.game is not None:
        line = f"{LINKED} {day} — {hd.quote(slot.game.name)}"
    elif slot.owner is not None:
        line = f"{TAKEN} {day} — {hd.quote(slot.author_name or '')}"
    else:
        line = f"{FREE} {day} — свободно"
    if slot.orgs:
        line += " (орги: " + ", ".join(hd.quote(org.name_mention) for org in slot.orgs) + ")"
    if slot.note:
        line += f" — {hd.quote(slot.note)}"
    return line


def render_digest(season: dto.Season, digests: Sequence[SlotDigest]) -> str:
    lines = [hd.bold(f"Изменения в расписании сезона {season.year}"), ""]
    lines.extend(render_digest_line(digest) for digest in digests)
    return "\n".join(lines)


def render_digest_line(digest: SlotDigest) -> str:
    line = f"{_day(digest.day)} — {'; '.join(_digest_parts(digest))}"
    if digest.by_superuser:
        line += " (изменено админом движка)"
    return line


def _digest_parts(digest: SlotDigest) -> list[str]:
    parts: list[str] = []
    if digest.added:
        parts.append("добавлена")
    if digest.removed:
        parts.append("удалена")
    if digest.moved:
        parts.append(f"перенесена с {_day(digest.date_before)} на {_day(digest.date_after)}")
    if digest.owner is not None:
        parts.append(f"занял {hd.quote(digest.owner)}")
    if digest.released:
        parts.append("освобождена")
    parts.extend(_content_parts(digest))
    return parts


def _content_parts(digest: SlotDigest) -> list[str]:
    parts: list[str] = []
    if digest.orgs_changed:
        orgs = ", ".join(hd.quote(org) for org in digest.orgs) if digest.orgs else "никого"
        parts.append(f"орги: {orgs}")
    if digest.note_changed:
        parts.append(f"заметка: {hd.quote(digest.note) if digest.note else 'убрана'}")
    if digest.game is not None:
        parts.append(f"привязана игра {hd.quote(digest.game)}")
    if digest.game_unlinked:
        parts.append("игра отвязана")
    return parts


def _day(day: date | None) -> str:
    return day.strftime(SLOT_DATE_FORMAT) if day is not None else "?"
