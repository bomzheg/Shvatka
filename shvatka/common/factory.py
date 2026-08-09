import typing

from adaptix import (
    Retort,
    TypeHint,
    validator,
    P,
    name_mapping,
    loader,
    Chain,
)
from adaptix.load_error import LoadError
from adaptix._internal.morphing.provider_template import ABCProxy
from dishka import Provider, Scope, provide
from telegraph.aio import Telegraph

from shvatka.common.url_factory import UrlFactory
from shvatka.core.models.dto import scn, action
from shvatka.core.models.dto import hints
from shvatka.core.utils import exceptions
from shvatka.core.utils.input_validation import validate_level_id, is_multiple_keys_normal
from shvatka.core.views.texts import INVALID_KEY_ERROR
from shvatka.tgbot.config.models.bot import BotConfig


class TelegraphProvider(Provider):
    scope = Scope.APP

    @provide
    def create_telegraph(self, bot_config: BotConfig) -> Telegraph:
        telegraph = Telegraph(access_token=bot_config.telegraph_token)
        return telegraph


class ConcreteProxy(ABCProxy):
    """Load/dump an abstract type as a fixed concrete one.

    ``ABCProxy`` parametrises its target with the generic args of the abstract
    type, which only works for a still-generic abstract like ``Sequence``.
    ``HintsList``/``Conditions`` are plain, already parametrised subclasses of
    ``Sequence[...]``, so the target type is complete as given.
    """

    def _get_proxy_target(self, tp: TypeHint) -> TypeHint:
        return self._impl


def flatten_legacy_tg_link(data):
    """Accept scenarios written before file_id/content_type were inlined.

    Older zips nested them under ``tg_link``; that key is unknown now, so
    without this the values would be silently dropped and the file would end
    up with no content_type at all.
    """
    if not isinstance(data, dict):
        return data
    tg_link = data.get("tg_link")
    if not isinstance(tg_link, dict):
        return data
    data = {k: v for k, v in data.items() if k != "tg_link"}
    data.setdefault("file_id", tg_link.get("file_id"))
    data.setdefault("content_type", tg_link.get("content_type"))
    return data


REQUIRED_GAME_RECIPES = [
    name_mapping(map={"__model_version__": "__model_version__"}),
    loader(hints.FileMetaLightweight, flatten_legacy_tg_link, Chain.FIRST),
    loader(hints.UploadedFileMeta, flatten_legacy_tg_link, Chain.FIRST),
    loader(hints.StoredFileMeta, flatten_legacy_tg_link, Chain.FIRST),
    loader(hints.FileMeta, flatten_legacy_tg_link, Chain.FIRST),
    loader(scn.HintsList, lambda x: scn.HintsList.parse(x), Chain.LAST),
    ConcreteProxy(
        scn.HintsList, list[hints.TimeHint]
    ),  # internal class, can be broken in next adaptix version
    loader(scn.Conditions, lambda x: scn.Conditions(x), Chain.LAST),
    ConcreteProxy(
        scn.Conditions, list[action.AnyCondition]
    ),  # internal class, can be broken in next adaptix version
]

VALIDATION_GAME_RECIPES = [
    validator(
        pred=P[scn.LevelScenario].id,
        func=lambda x: validate_level_id(x) is not None,
        error=lambda x: typing.cast(
            LoadError,
            exceptions.ScenarioNotCorrect(name_id=x, text=f"name_id ({x}) not correct"),
        ),
    ),
    validator(
        pred=P[scn.LevelScenario].keys,
        func=is_multiple_keys_normal,
        error=lambda x: typing.cast(
            LoadError,
            exceptions.ScenarioNotCorrect(notify_user=INVALID_KEY_ERROR, text="invalid keys"),
        ),
    ),
]


class DCFProvider(Provider):
    scope = Scope.APP

    @provide
    def create_retort(self) -> Retort:
        retort = Retort(recipe=[*REQUIRED_GAME_RECIPES, *VALIDATION_GAME_RECIPES])
        return retort


class UrlProvider(Provider):
    scope = Scope.APP

    url_factory = provide(UrlFactory)
