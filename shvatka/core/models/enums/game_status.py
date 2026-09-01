from __future__ import annotations

import enum


class GameStatus(str, enum.Enum):
    underconstruction = "underconstruction"
    ready = "ready"
    getting_waivers = "getting_waivers"
    started = "started"
    finished = "finished"
    complete = "complete"


status_desc = {
    GameStatus.underconstruction: "в процессе создания",
    GameStatus.ready: "полностью готова",
    GameStatus.getting_waivers: "сбор вейверов",
    GameStatus.started: "началась",
    GameStatus.finished: "все команды финишировали",
    GameStatus.complete: "завершена",
}
ACTIVE_STATUSES = (GameStatus.getting_waivers, GameStatus.started, GameStatus.finished)
ADMIN_MANAGEABLE_STATUSES = (*ACTIVE_STATUSES, GameStatus.complete)
"""Games an admin may see at all — and then only their status, never their
content. A game still being written (``underconstruction``, ``ready``)
belongs to its author alone and stays invisible to the admin panel."""
EDITABLE_STATUSES = (
    GameStatus.underconstruction,
    GameStatus.ready,
    GameStatus.getting_waivers,
)
PLAYED_STATUSES = (GameStatus.started, GameStatus.finished, GameStatus.complete)
"""Statuses a game only reaches by having been played. Everything a run
produces — level times, typed keys, events, timers — exists exactly for the
games that got this far."""
REWOUND_STATUSES = (
    GameStatus.getting_waivers,
    GameStatus.ready,
    GameStatus.underconstruction,
)
"""Statuses that put a game back *before* its run. Moving a played game into
one of them is the admin undoing a start, and the only moment the run's data
may be swept (see ``AdminChangeGameStatusInteractor``)."""
