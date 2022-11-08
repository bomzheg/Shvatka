from datetime import date, datetime, time
from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from db.dao import GameDao
from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.scheduler import Scheduler
from shvatka.services import game
from shvatka.services.game import get_game, plain_start
from shvatka.utils.datetime_utils import TIME_FORMAT, tz_game
from tgbot.states import MyGamesPanel, GameEditSG, GameSchedule


async def select_my_game(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    await c.answer()
    data = manager.dialog_data
    if not isinstance(data, dict):
        data = {}
    data["my_game_id"] = int(item_id)
    await manager.update(data)
    await manager.switch_to(MyGamesPanel.game_menu)


async def start_schedule_game(c: CallbackQuery, widget: Button, manager: DialogManager):
    await c.answer()
    game_id = manager.dialog_data["my_game_id"]
    await manager.start(GameSchedule.date, data={"my_game_id": int(game_id)})


async def show_scn(c: CallbackQuery, widget: Button, manager: DialogManager):
    await c.answer()
    game_id = manager.dialog_data["my_game_id"]
    await manager.start(GameEditSG.current_levels, data={"game_id": int(game_id)})


async def start_waivers(c: CallbackQuery, widget: Button, manager: DialogManager):
    await c.answer()
    context_data = manager.middleware_data
    data = manager.dialog_data
    player: dto.Player = context_data["player"]
    game_dao: GameDao = context_data["dao"].game
    game_ = await get_game(int(data["my_game_id"]), player, game_dao)
    await game.start_waivers(game_, player, game_dao)


async def select_date(c: CallbackQuery, widget, manager: DialogManager, selected_date: date):
    await c.answer()
    data = manager.dialog_data
    if not isinstance(data, dict):
        data = {}
    data["scheduled_date"] = selected_date.isoformat()
    await manager.update(data)
    await manager.switch_to(GameSchedule.time)


async def process_time_message(m: Message, dialog_: Any, manager: DialogManager) -> None:
    try:
        time_ = datetime.strptime(m.text, TIME_FORMAT).time()
    except ValueError:
        await m.answer("Некорректный формат времени. Пожалуйста введите время в формате ЧЧ:ММ")
        return
    data = manager.dialog_data
    data["scheduled_time"] = time_.isoformat()
    await manager.update(data)
    await manager.switch_to(GameSchedule.confirm)


async def schedule_game(c: CallbackQuery, widget: Button, manager: DialogManager):
    at = datetime.combine(
        date=date.fromisoformat(manager.dialog_data["scheduled_date"]),
        time=time.fromisoformat(manager.dialog_data["scheduled_time"]),
        tzinfo=tz_game,
    )
    game_id = int(manager.dialog_data["my_game_id"])
    player: dto.Player = manager.middleware_data["player"]
    dao: HolderDao = manager.middleware_data["dao"]
    scheduler: Scheduler = manager.middleware_data["scheduler"]
    await plain_start(
        game=await dao.game.get_by_id(game_id, player),
        author=player,
        start_at=at,
        dao=dao.game,
        scheduler=scheduler,
    )
    await c.answer("Запланировано успешно")
    await manager.done()
