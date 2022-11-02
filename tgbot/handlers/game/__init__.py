from aiogram import Router

from tgbot.handlers.game import editor, play


def setup() -> Router:
    router = Router(name=__name__)
    router.include_router(editor.setup())
    router.include_router(play.setup())
    return router
