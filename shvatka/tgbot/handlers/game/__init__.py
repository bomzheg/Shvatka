from aiogram import Router

from shvatka.tgbot.handlers.game import add_organizer, organizer
from shvatka.tgbot.handlers.game import play, waivers


def setup() -> Router:
    router = Router(name=__name__)
    router.include_router(play.setup())
    router.include_router(add_organizer.setup())
    router.include_router(organizer.setup())
    router.include_router(waivers.setup())
    return router
