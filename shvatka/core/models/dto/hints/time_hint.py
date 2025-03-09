from dataclasses import dataclass

from shvatka.core.utils import exceptions
from .hint_part import AnyHint


@dataclass
class TimeHint:
    time: int
    hint: list[AnyHint]

    def __post_init__(self):
        _check_hint_not_empty(self.hint)

    def get_guids(self) -> list[str]:
        guids = []
        for hint in self.hint:
            guids.extend(hint.get_guids())
        return guids

    @property
    def hints_count(self) -> int:
        return len(self.hint)

    def update_time(self, new_time: int) -> None:
        if self.time == new_time:
            return
        if not self.can_update_time():
            raise exceptions.LevelError(
                text="Невозможно отредактировать время выхода загадки уровня"
            )
        if new_time == 0:
            raise exceptions.LevelError(text="Нельзя заменить таким способом загадку уровня")
        self.time = new_time

    def update_hint(self, new_hint: list[AnyHint]) -> None:
        _check_hint_not_empty(new_hint)
        self.hint = new_hint

    def can_update_time(self) -> bool:
        return self.time != 0


@dataclass
class EnumeratedTimeHint(TimeHint):
    number: int


def _check_hint_not_empty(new_hint: list[AnyHint]) -> None:
    if not new_hint:
        raise exceptions.LevelError(
            text="Нельзя установить пустой список подсказок. Вероятно нужно было удалить?"
        )
