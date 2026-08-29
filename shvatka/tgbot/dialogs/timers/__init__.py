from aiogram import Router

from shvatka.tgbot.dialogs.timers.dialogs import timer_dialog, timers_dialog


def setup(router: Router):
    router.include_router(timers_dialog)
    router.include_router(timer_dialog)
