import typing

import adaptix
import dataclass_factory
from adaptix import (
    Retort,
    validator,
    P,
    name_mapping,
    loader,
    Chain,
    dumper,
)
from adaptix.load_error import LoadError
from adaptix._internal.morphing.provider_template import ABCProxy
from dataclass_factory import Schema, NameStyle
from dishka import Provider, Scope, provide
from telegraph.aio import Telegraph

from shvatka.common.url_factory import UrlFactory
from shvatka.core.models.dto import scn
from shvatka.core.models.dto.action import AnyCondition
from shvatka.core.models.dto.scn import HintsList, TimeHint, Conditions
from shvatka.core.models.schems import schemas
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


REQUIRED_GAME_RECIPES = [
    loader(HintsList, lambda x: HintsList.parse(x), Chain.LAST),
    ABCProxy(HintsList, list[TimeHint]),  # internal class, can be broken in next version adaptix
    loader(Conditions, lambda x: Conditions(x), Chain.LAST),
    ABCProxy(
        Conditions, list[AnyCondition]
    ),  # internal class, can be broken in next version adaptix
    dumper(set, lambda x: tuple(x)),
]


class DCFProvider(Provider):
    scope = Scope.APP

    @provide
    def create_dataclass_factory(self) -> dataclass_factory.Factory:
        dcf = dataclass_factory.Factory(
            schemas=schemas,  # type:ignore[arg-type]
            default_schema=Schema(name_style=NameStyle.kebab),
        )
        return dcf

    @provide
    def create_retort(self) -> Retort:
        retort = Retort(
            recipe=[
                name_mapping(
                    name_style=adaptix.NameStyle.LOWER_KEBAB,
                ),
                *REQUIRED_GAME_RECIPES,
                validator(
                    pred=P[scn.LevelScenario].id,
                    func=lambda x: validate_level_id(x) is not None,
                    error=lambda x: typing.cast(
                        LoadError,
                        exceptions.ScenarioNotCorrect(
                            name_id=x, text=f"name_id ({x}) not correct"
                        ),
                    ),
                ),
                validator(
                    pred=P[scn.LevelScenario].keys,
                    func=is_multiple_keys_normal,
                    error=lambda x: typing.cast(
                        LoadError,
                        exceptions.ScenarioNotCorrect(
                            notify_user=INVALID_KEY_ERROR, text="invalid keys"
                        ),
                    ),
                ),
            ]
        )
        return retort


class UrlProvider(Provider):
    scope = Scope.APP

    url_factory = provide(UrlFactory)
