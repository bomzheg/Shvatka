from aiogram import Router

from shvatka.tgbot.dialogs.timers.dialogs import timers_dialog, timer_dialog


def setup(router: Router):
    router.include_router(timers_dialog)
    router.include_router(timer_dialog)
