from aiogram import Router

from src.tgbot.handlers.game import editor, add_organizer, organizer
from src.tgbot.handlers.game import play, stat, waivers


def setup() -> Router:
    router = Router(name=__name__)
    router.include_router(editor.setup())
    router.include_router(play.setup())
    router.include_router(add_organizer.setup())
    router.include_router(organizer.setup())
    router.include_router(stat.setup())
    router.include_router(waivers.setup())
    return router
