import adaptix
import dataclass_factory
from adaptix import Retort, validator, P, name_mapping, loader, Chain, as_is_loader, constructor, bound
from dataclass_factory import Schema, NameStyle
from dishka import Provider, Scope, provide
from pyrogram.errors.exceptions.all import exceptions
from telegraph.aio import Telegraph

from shvatka.common.url_factory import UrlFactory
from shvatka.core.models.dto import scn
from shvatka.core.models.dto.scn import HintsList, TimeHint
from shvatka.core.models.schems import schemas
from shvatka.core.utils.input_validation import validate_level_id, is_multiple_keys_normal
from shvatka.core.views.texts import INVALID_KEY_ERROR
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.views.hint_factory.hint_parser import HintParser


class TelegraphProvider(Provider):
    scope = Scope.APP

    @provide
    def create_telegraph(self, bot_config: BotConfig) -> Telegraph:
        telegraph = Telegraph(access_token=bot_config.telegraph_token)
        return telegraph


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
        internal_retort = Retort(
            recipe=[
                name_mapping(name_style=adaptix.NameStyle.LOWER_KEBAB),
            ]
        )
        retort = Retort(
            recipe=[
                name_mapping(
                    name_style=adaptix.NameStyle.LOWER_KEBAB,
                ),

                validator(
                    pred=P[scn.LevelScenario].id,
                    func=lambda x: validate_level_id(x) is not None,
                    error=lambda x: exceptions.ScenarioNotCorrect(name_id=x, text=f"name_id ({x}) not correct")
                ),
                validator(
                    pred=P[scn.LevelScenario].keys,
                    func=is_multiple_keys_normal,
                    error=lambda x: exceptions.ScenarioNotCorrect(notify_user=INVALID_KEY_ERROR, text="invalid keys")
                ),
            ]
        )
        return retort


class UrlProvider(Provider):
    scope = Scope.APP

    url_factory = provide(UrlFactory)
