from __future__ import annotations

from decimal import Decimal
from enum import Enum
from fractions import Fraction
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeVar
from uuid import UUID

from aiogram.filters.base import Filter
from aiogram.types import InlineQuery
from magic_filter import MagicFilter
from pydantic import BaseModel

T = TypeVar("T", bound="InlineData")

MAX_CALLBACK_LENGTH: int = 64


class InlineDataException(Exception):
    pass


class InlineData(BaseModel):
    """
    Base class for inline data wrapper

    This class should be used as super-class of user-defined callbacks.

    The class-keyword :code:`prefix` is required to define prefix
    and also the argument :code:`sep` can be passed to define separator (default is :code:`:`).
    """

    if TYPE_CHECKING:
        __separator__: ClassVar[str]
        """Data separator (default is :code:`:`)"""
        __prefix__: ClassVar[str]
        """Callback prefix"""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        if "prefix" not in kwargs:
            raise ValueError(
                f"prefix required, usage example: "
                f"`class {cls.__name__}(InlineData, prefix='my_callback'): ...`"
            )
        cls.__separator__ = kwargs.pop("sep", ":")
        cls.__prefix__ = kwargs.pop("prefix")
        if cls.__separator__ in cls.__prefix__:
            raise ValueError(
                f"Separator symbol {cls.__separator__!r} can not be used "
                f"inside prefix {cls.__prefix__!r}"
            )
        super().__init_subclass__(**kwargs)

    def _encode_value(self, key: str, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, Enum):
            return str(value.value)
        if isinstance(value, int | str | float | Decimal | Fraction | UUID):
            return str(value)
        raise ValueError(
            f"Attribute {key}={value!r} of type {type(value).__name__!r}"
            f" can not be packed to inline data"
        )

    def pack(self) -> str:
        """
        Generate inline data string

        :return: valid inline data for Telegram Bot API
        """
        result = [self.__prefix__]
        for key, value in self.model_dump().items():
            encoded = self._encode_value(key, value)
            if self.__separator__ in encoded:
                raise ValueError(
                    f"Separator symbol {self.__separator__!r} can not be used "
                    f"in value {key}={encoded!r}"
                )
            result.append(encoded)
        inline_data = self.__separator__.join(result)
        if len(inline_data.encode()) > MAX_CALLBACK_LENGTH:
            raise ValueError(
                f"Resulted inline data is too long! "
                f"len({inline_data!r}.encode()) > {MAX_CALLBACK_LENGTH}"
            )
        return inline_data

    @classmethod
    def unpack(cls: type[T], value: str) -> T:
        """
        Parse inline data string

        :param value: value from Telegram
        :return: instance of InlineData
        """
        prefix, *parts = value.split(cls.__separator__)
        names = cls.model_fields.keys()
        if len(parts) != len(names):
            raise TypeError(
                f"Inline data {cls.__name__!r} takes {len(names)} arguments "
                f"but {len(parts)} were given"
            )
        if prefix != cls.__prefix__:
            raise ValueError(f"Bad prefix ({prefix!r} != {cls.__prefix__!r})")
        payload = {}
        for k, v in zip(names, parts):  # type: str, str | None
            if (field := cls.model_fields.get(k)) and v == "" and not field.is_required():
                v = None
            payload[k] = v
        return cls(**payload)

    @classmethod
    def filter(cls, rule: MagicFilter | None = None) -> InlineQueryFilter:
        """
        Generates a filter for inline query with rule

        :param rule: magic rule
        :return: instance of filter
        """
        return InlineQueryFilter(inline_data=cls, rule=rule)


class InlineQueryFilter(Filter):
    """
    This filter helps to handle inline query.

    Should not be used directly, you should create the instance of this filter
    via inline data instance
    """

    def __init__(
        self,
        *,
        inline_data: type[InlineData],
        rule: MagicFilter | None = None,
    ) -> None:
        """
        :param inline_data: Expected type of inline data
        :param rule: Magic rule
        """
        self.inline_data = inline_data
        self.rule = rule

    def __str__(self) -> str:
        return self._signature_to_string(
            inline_data=self.inline_data,
            rule=self.rule,
        )

    async def __call__(self, query: InlineQuery) -> Literal[False] | dict[str, Any]:
        if not isinstance(query, InlineQuery) or not query.query:
            return False
        try:
            inline_data = self.inline_data.unpack(query.query)
        except (TypeError, ValueError):
            return False

        if self.rule is None or self.rule.resolve(inline_data):
            return {"inline_data": inline_data}
        return False
