from __future__ import annotations

import enum


class GameStatus(str, enum.Enum):
    underconstruction = 'underconstruction'
    ready = 'ready'
    getting_waivers = 'getting_waivers'
    started = 'started'
    finished = 'finished'
    complete = 'complete'


status_desc = {
    GameStatus.underconstruction: 'в процессе создания',
    GameStatus.ready: 'полностью готова',
    GameStatus.getting_waivers: 'сбор вейверов',
    GameStatus.started: 'началась',
    GameStatus.finished: 'все команды финишировали',
    GameStatus.complete: 'завершена'
}
active_statuses = [
    GameStatus.getting_waivers,
    GameStatus.started,
    GameStatus.finished
]
