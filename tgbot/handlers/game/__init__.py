from aiogram import Dispatcher

from tgbot.handlers.game import editor


def setup(dp: Dispatcher):
    editor.setup(dp)
