import dataclass_factory
from dataclass_factory import Schema, NameStyle
from telegraph.aio import Telegraph

from src.shvatka.models.schems import schemas
from src.tgbot.config.models.bot import BotConfig


def create_telegraph(bot_config: BotConfig) -> Telegraph:
    telegraph = Telegraph(access_token=bot_config.telegraph_token)
    return telegraph


def create_dataclass_factory():
    dcf = dataclass_factory.Factory(
        schemas=schemas, default_schema=Schema(name_style=NameStyle.kebab)
    )
    return dcf
