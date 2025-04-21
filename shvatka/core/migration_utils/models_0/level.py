import typing
from collections.abc import Sequence, Iterable
from dataclasses import dataclass, field


from shvatka.core.utils import exceptions
from .hint_part import AnyHint
from .time_hint import TimeHint

SHKey: typing.TypeAlias = str


@dataclass(frozen=True)
class BonusKey:
    text: str
    bonus_minutes: float

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BonusKey):
            return NotImplemented
        return self.text == other.text

    def __hash__(self) -> int:
        return hash(self.text)


class HintsList(Sequence[TimeHint]):
    def __init__(self, hints_: list[TimeHint]):
        self.verify(hints_)
        self.hints = hints_

    @classmethod
    def parse(cls, hints_: list[TimeHint]):
        return cls(cls.normalize(hints_))

    @staticmethod
    def normalize(hints_: list[TimeHint]) -> list[TimeHint]:
        hint_map: dict[int, list[AnyHint]] = {}
        for hint in hints_:
            if not hint.hint:
                continue
            hint_map.setdefault(hint.time, []).extend(hint.hint)
        return [TimeHint(k, v) for k, v in sorted(hint_map.items(), key=lambda x: x[0])]

    @staticmethod
    def verify(hints_: Iterable[TimeHint]) -> None:
        current_time = -1
        times: set[int] = set()
        for hint in hints_:
            if hint.time in times:
                raise exceptions.LevelError(
                    text=f"Contains multiple times hints for time {hint.time}"
                )
            if hint.time <= current_time:
                raise exceptions.LevelError(text="hints are not sorted")
            current_time = hint.time
            times.add(hint.time)
            if not hint.hint:
                raise exceptions.LevelError(text=f"There is no hint for time {hint.time}")
        if 0 not in times:
            raise exceptions.LevelError(text="There is no hint for 0 min")


@dataclass
class LevelScenario:
    id: str
    time_hints: HintsList
    keys: set[SHKey] = field(default_factory=set)
    bonus_keys: set[BonusKey] = field(default_factory=set)
    __model_version__: typing.Literal[0] = 0
