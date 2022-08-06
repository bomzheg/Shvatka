from aiogram import Dispatcher

from app.handlers.game import editor


def setup(dp: Dispatcher):
    editor.setup(dp)
