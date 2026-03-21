import asyncio
import typing

from dishka import make_async_container

from shvatka.common import setup_logging
from shvatka.common.config.parser.paths import common_get_paths
from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.core.models.dto import action
from shvatka.infrastructure.clients.file_gateway import BotFileGateway
from shvatka.infrastructure.db.dao import FileInfoDao
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.di import get_providers
from shvatka.tgbot.main_factory import get_bot_specific_providers


async def main():
    paths = common_get_paths("CRAWLER_PATH")

    setup_logging(paths)
    dishka = make_async_container(
        *get_providers("CRAWLER_PATH"),
        *get_bot_specific_providers(),
    )
    try:
        async with dishka() as rd:
            dao = await rd.get(HolderDao)
            levels = sorted([l.scenario for l in await dao.level._get_all() if l.scenario.conditions.get_effects_key_conditions()], key=lambda l: l.id)
            for level in levels:
                effects =  level.conditions.get_effects_key_conditions()
                bonus_only_effects = [e for e in effects if is_effect_only_bonus(e.effect)]
                if not bonus_only_effects:
                    continue
                print(level.id)
                bonuses = sorted(bonus_only_effects, key=lambda b: next(iter(b.keys)))
                for bk in bonuses:
                    print(next(iter(bk.keys)), bk.effect.bonus_minutes)
                print()

    finally:
        await dishka.close()


def is_effect_only_bonus(effect: action.Effects) -> bool:
    if effect.bonus_minutes == 0:
        return False
    else:
        if effect.level_up:
            return False
        if effect.hints_:
            return False
        return True


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
