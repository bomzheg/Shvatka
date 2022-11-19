from aiogram import Router

from tgbot.handlers.game import editor, play, add_organizer, level_testing


def setup() -> Router:
    router = Router(name=__name__)
    router.include_router(editor.setup())
    router.include_router(play.setup())
    router.include_router(add_organizer.setup())
    router.include_router(level_testing.setup())
    return router
