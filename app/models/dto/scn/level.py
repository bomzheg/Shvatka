from __future__ import annotations

import typing
from typing import List

from aiogram.utils.markdown import html_decoration as hd

from app.utils.exceptions import ScenarioNotCorrect
from app.utils.input_validation import is_level_id_correct, is_key_normal
from .file_content import FileContent
from .hint_container import BaseHint, FileMixin

TimeHint = typing.NamedTuple('TimeHint', [('time', int), ('hint', list[BaseHint])])


class LevelScenario:
    def __init__(
        self,
        user_id: int,
        level_id: str,
        keys: set[str] = None,
        time_hints: list[TimeHint] = None,
        penalty_hints: typing.Optional[list] = None
    ):
        self.level_id = level_id
        self.user_id = user_id
        self._keys = set() if keys is None else keys

        self.time_hints: list[TimeHint] = [] if time_hints is None \
            else sorted(time_hints, key=lambda x: int(x.time))

        self.penalty_hints = [] if penalty_hints is None else penalty_hints

    def set_keys(self, keys: typing.Iterable):
        if keys is None:
            self._keys = set()
        elif isinstance(keys, set):
            self._keys = keys
        else:
            self._keys = set(keys)

    def add_keys(self, key):
        if isinstance(key, list):
            self._keys.update(set(key))
        else:
            self._keys.add(key)

    def get_keys(self):
        return self._keys

    keys = property(get_keys, set_keys)

    def get_json_serializable(self):
        return {
            "__level__": True,
            "id": self.level_id,
            "author_ID": self.user_id,
            "keys": [{'type': "default", "value": key} for key in self._keys],
            "time_hints": [
                {
                    "time": time,
                    "parts": [hint_part.get_json_serializable() for hint_part in hint]
                } for time, hint in self.time_hints
            ],
            "penalty_hints": []
        }

    @classmethod
    def parse_as_level(cls, dct: dict) -> LevelScenario:
        if "__level__" not in dct:
            raise ScenarioNotCorrect

        author_id = dct["author_ID"]
        if not isinstance(author_id, int):
            try:
                author_id = int(author_id)
            except (TypeError, ValueError):
                raise ScenarioNotCorrect

        level_id = dct["id"].strip()
        if not is_level_id_correct(level_id):
            raise ScenarioNotCorrect(
                f"Предложенный id уровня {hd.quote(level_id)} не соответствует требованиям",
                user_id=author_id
            )

        keys = {key["value"] for key in dct["keys"] if key["type"] == "default"}
        if not all(is_key_normal(key) for key in keys):
            raise ScenarioNotCorrect(
                f"Предложенные ключи {keys} для уровня {hd.quote(level_id)} не соответствует требованиям",
                user_id=author_id
            )

        try:
            hints = cls.parse_hints(dct)
        except (TypeError, ValueError) as e:
            raise ScenarioNotCorrect(
                f"в уровне {hd.quote(level_id)} указано время подсказок не числовом виде",
                user_id=author_id,
                level_id=level_id,
            ) from e
        except ScenarioNotCorrect as e:
            e.level_id = level_id
            raise
        penalty_hints = dct["penalty_hints"]
        new_lvl = cls(author_id, level_id, keys, hints, penalty_hints)
        return new_lvl

    @classmethod
    def parse_hints(cls, dct: dict) -> list[TimeHint]:
        return [
            TimeHint(
                int(hint["time"]),
                LevelScenario.parse_hints_parts(hint)
            ) for hint in dct["time_hints"]
        ]

    @classmethod
    def parse_hints_parts(cls, hint: dict) -> list[BaseHint]:
        parsed_parts = [BaseHint.parse_as_hint(hint_parts) for hint_parts in hint["parts"]]
        return parsed_parts

    def hints_count(self):
        return sum([
            len(self.time_hints),
            len(self.penalty_hints),
        ])

    def get_all_files(self) -> List[FileContent]:
        result = []
        for _, hint_parts in self.time_hints:
            for hint_part in hint_parts:
                if isinstance(hint_part, FileMixin):
                    file = hint_part.file
                    if not file.content:
                        file.content = hint_part.content  # noqa
                    result.append(file)
        return result

    def __repr__(self):
        rez = (
            f"LevelScenario id: {self.level_id} "
            f"author: {self.user_id} "
            f"keys: {self._keys} "
            f"time_hints: {self.time_hints}"
        )
        return rez
