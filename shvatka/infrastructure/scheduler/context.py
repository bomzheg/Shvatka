from dishka import AsyncContainer
from dishka.integrations.base import wrap_injection


class ScheduledContextHolder:
    """
    ATTENTION!
    GLOBAL VARIABLE!
    """
    dishka: AsyncContainer


def inject(func):
    async def wrapper(*args, **kwargs):
        async with ScheduledContextHolder.dishka() as request_dishka:
            wrapped = wrap_injection(
                func=func,
                remove_depends=True,
                container_getter=lambda _, __: request_dishka,
                is_async=True,
            )
            return await wrapped(*args, **kwargs)

    return wrapper
