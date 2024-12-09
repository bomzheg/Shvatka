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
from adaptix import Retort, Mediator, Dumper
from adaptix._internal.morphing.iterable_provider import IterableProvider
from adaptix._internal.morphing.request_cls import DumperRequest, DebugTrailRequest
from adaptix._internal.provider.location import GenericParamLoc
from dataclass_factory import Schema, NameStyle
from dishka import Provider, Scope, provide
from telegraph.aio import Telegraph

from shvatka.common.url_factory import UrlFactory
from shvatka.core.models.dto import scn, action
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

class FixedIterableProvider(IterableProvider):
    def provide_dumper(self, mediator: Mediator, request: DumperRequest) -> Dumper:
        norm, arg = self._fetch_norm_and_arg(request)

        arg_dumper = mediator.mandatory_provide(
            request.append_loc(GenericParamLoc(type=arg, generic_pos=0)),
            lambda x: "Cannot create dumper for iterable. Dumper for element cannot be created",
        )
        debug_trail = mediator.mandatory_provide(DebugTrailRequest(loc_stack=request.loc_stack))
        return mediator.cached_call(
            self._make_dumper,
            origin=norm.origin,
            iter_factory=list,
            arg_dumper=arg_dumper,
            debug_trail=debug_trail,
        )

REQUIRED_GAME_RECIPES = [
    name_mapping(map={"__model_version__": "__model_version__"}),
    loader(HintsList, lambda x: HintsList.parse(x), Chain.LAST),
    ABCProxy(HintsList, list[TimeHint]),  # internal class, can be broken in next adaptix version
    loader(Conditions, lambda x: Conditions(x), Chain.LAST),
    ABCProxy(
        Conditions, list[AnyCondition]
    ),  # internal class, can be broken in next adaptix version
    FixedIterableProvider(),
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
