from dishka import AsyncContainer

from shvatka.infrastructure.db.dao.holder import HolderDao


async def warm_up(dishka: AsyncContainer) -> None:
    async with dishka() as request_dishka:
        await request_dishka.get(HolderDao)
