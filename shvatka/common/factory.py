import typing

from adaptix import (
    Chain,
    P,
    Retort,
    TypeHint,
    loader,
    name_mapping,
    validator,
)
from adaptix._internal.morphing.provider_template import ABCProxy
from adaptix.load_error import LoadError
from dishka import Provider, Scope, provide
from telegraph.aio import Telegraph

from shvatka.common.docs import DocsUrlFactory
from shvatka.common.url_factory import UrlFactory
from shvatka.core.models.dto import action, hints, scn
from shvatka.core.utils import exceptions
from shvatka.core.utils.input_validation import is_multiple_keys_normal, validate_level_id
from shvatka.core.views.texts import INVALID_KEY_ERROR
from shvatka.tgbot.config.models.bot import BotConfig


class TelegraphProvider(Provider):
    scope = Scope.APP

    @provide
    def create_telegraph(self, bot_config: BotConfig) -> Telegraph:
        return Telegraph(access_token=bot_config.telegraph_token)


class ConcreteProxy(ABCProxy):
    def _get_proxy_target(self, tp: TypeHint) -> TypeHint:
        return self._impl


def flatten_legacy_tg_link(data):
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
        error=lambda _: typing.cast(
            LoadError,
            exceptions.ScenarioNotCorrect(notify_user=INVALID_KEY_ERROR, text="invalid keys"),
        ),
    ),
]


class DCFProvider(Provider):
    scope = Scope.APP

    @provide
    def create_retort(self) -> Retort:
        return Retort(recipe=[*REQUIRED_GAME_RECIPES, *VALIDATION_GAME_RECIPES])


class UrlProvider(Provider):
    scope = Scope.APP

    url_factory = provide(UrlFactory)
    docs_url_factory = provide(DocsUrlFactory)
