from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from shvatka.core.season import dto
from shvatka.core.season.rules import SlotDigest


@dataclass(frozen=True)
class Announcement:
    """Where the schedule message lives, so it can be edited and unpinned later."""

    chat_id: int
    message_id: int


class SeasonAnnouncer(Protocol):
    """A sibling of `GameLogWriter` that can hand the message back.

    `GameLogWriter.log` returns nothing and the complex writer swallows errors,
    so it cannot give up the `message_id` this feature has to store, edit and
    later unpin. See SHEP-0003.
    """

    async def publish(self, season: dto.Season) -> Announcement | None:
        """Send the schedule and pin it. `None` when nothing was announced."""
        raise NotImplementedError

    async def update(self, season: dto.Season) -> None:
        """Edit the stored message in place. A no-op when there is none."""
        raise NotImplementedError

    async def announce_digest(self, season: dto.Season, digests: Sequence[SlotDigest]) -> None:
        """Post the day's collapsed changes as a new message."""
        raise NotImplementedError

    async def close(self, season: dto.Season) -> None:
        """Release the pin once the season is over. The message itself stays."""
        raise NotImplementedError
