from aiogram import Router

from tgbot.handlers.game import editor


def setup() -> Router:
    router = Router(name=__name__)
    router.include_router(editor.setup())
    return router
