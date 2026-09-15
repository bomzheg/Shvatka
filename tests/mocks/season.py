from collections.abc import Sequence

from shvatka.core.models import dto
from shvatka.core.season import dto as season_dto
from shvatka.core.season.interactors import SyncLinkedSlotInteractor
from shvatka.core.season.rules import SlotDigest
from shvatka.core.views.season import Announcement, SeasonAnnouncer

MOCK_CHAT_ID = -1001
MOCK_MESSAGE_ID = 42


class SeasonAnnouncerMock(SeasonAnnouncer):
    """Remembers what would have reached the channel, and hands a message back."""

    def __init__(self) -> None:
        self.published: list[season_dto.Season] = []
        self.updated: list[season_dto.Season] = []
        self.digests: list[tuple[season_dto.Season, Sequence[SlotDigest]]] = []
        self.closed: list[season_dto.Season] = []

    async def publish(self, season: season_dto.Season) -> Announcement | None:
        self.published.append(season)
        return Announcement(chat_id=MOCK_CHAT_ID, message_id=MOCK_MESSAGE_ID)

    async def update(self, season: season_dto.Season) -> None:
        self.updated.append(season)

    async def announce_digest(
        self, season: season_dto.Season, digests: Sequence[SlotDigest]
    ) -> None:
        self.digests.append((season, list(digests)))

    async def close(self, season: season_dto.Season) -> None:
        self.closed.append(season)

    def clear(self) -> None:
        self.published.clear()
        self.updated.clear()
        self.digests.clear()
        self.closed.clear()


class SlotSyncMock(SyncLinkedSlotInteractor):
    def __init__(self) -> None:
        self.calls: list[tuple[dto.Game, dto.Player]] = []

    async def __call__(self, game: dto.Game, actor: dto.Player) -> None:
        self.calls.append((game, actor))
