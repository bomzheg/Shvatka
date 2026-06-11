import typing

import adaptix
import dataclass_factory
from adaptix import (
    Retort,
    validator,
    P,
    name_mapping,
    loader,
    dumper,
    Chain,
)
from adaptix.load_error import LoadError
from adaptix._internal.morphing.provider_template import ABCProxy
from dataclass_factory import Schema, NameStyle
from dishka import Provider, Scope, provide
from telegraph.aio import Telegraph

from shvatka.common.url_factory import UrlFactory
from shvatka.core.models.dto import scn, action
from shvatka.core.models.dto import hints
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
    name_mapping(map={"__model_version__": "__model_version__"}),
    loader(scn.HintsList, lambda x: scn.HintsList.parse(x), Chain.LAST),
    ABCProxy(
        scn.HintsList, list[hints.TimeHint]
    ),  # internal class, can be broken in next adaptix version
    loader(scn.Conditions, lambda x: scn.Conditions(x), Chain.LAST),
    ABCProxy(
        scn.Conditions, list[action.AnyCondition]
    ),  # internal class, can be broken in next adaptix version
]


def create_game_retort() -> Retort:
    """adaptix Retort for game scenarios using plain snake_case field names.

    Used by the API for both parsing incoming scenarios and dumping them back, so the
    request and response shapes are symmetric. Unlike :class:`DCFProvider` (legacy, kebab),
    this does not pull in dataclass_factory.
    """
    return Retort(
        recipe=[
            *REQUIRED_GAME_RECIPES,
            dumper(scn.HintsList, lambda x: x.hints),
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
                    exceptions.ScenarioNotCorrect(
                        notify_user=INVALID_KEY_ERROR, text="invalid keys"
                    ),
                ),
            ),
        ]
    )


GAME_SCENARIO_RETORT: Retort = create_game_retort()


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
