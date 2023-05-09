from datetime import date, datetime, time
from io import BytesIO
from typing import Any

from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from dataclass_factory import Factory

from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.models import dto
from shvatka.core.services import game
from shvatka.core.services.game import rename_game, get_game, get_full_game
from shvatka.core.services.game_stat import get_game_stat
from shvatka.core.services.scenario.scn_zip import pack_scn
from shvatka.core.utils.datetime_utils import TIME_FORMAT, tz_game
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import states
from shvatka.tgbot.views.results.level_times import export_results


async def select_my_game(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    await c.answer()
    data = manager.dialog_data
    if not isinstance(data, dict):
        data = {}
    data["my_game_id"] = int(item_id)
    await manager.switch_to(states.MyGamesPanelSG.game_menu)


async def select_game(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    await c.answer()
    data = manager.dialog_data
    if not isinstance(data, dict):
        data = {}
    data["game_id"] = int(item_id)
    await manager.switch_to(states.CompletedGamesPanelSG.game)


async def start_schedule_game(c: CallbackQuery, widget: Button, manager: DialogManager):
    await c.answer()
    game_id = manager.dialog_data["my_game_id"]
    await manager.start(states.GameScheduleSG.date, data={"my_game_id": int(game_id)})


async def cancel_scheduled_game(c: CallbackQuery, widget: Button, manager: DialogManager):
    await c.answer()
    game_id = manager.dialog_data["my_game_id"]
    player: dto.Player = manager.middleware_data["player"]
    dao: HolderDao = manager.middleware_data["dao"]
    game_ = await game.get_game(id_=game_id, dao=dao.game)
    scheduler: Scheduler = manager.middleware_data["scheduler"]
    await game.cancel_planed_start(game=game_, author=player, scheduler=scheduler, dao=dao.game)


async def show_scn(c: CallbackQuery, widget: Button, manager: DialogManager):
    await c.answer()
    game_id = manager.dialog_data["my_game_id"]
    await manager.start(states.GameEditSG.current_levels, data={"game_id": int(game_id)})


async def show_zip_scn(c: CallbackQuery, widget: Button, manager: DialogManager):
    await c.answer()
    game_id = manager.dialog_data["game_id"]
    await common_show_zip(c, game_id, manager)


async def show_my_zip_scn(c: CallbackQuery, widget: Button, manager: DialogManager):
    await c.answer()
    game_id = manager.dialog_data["my_game_id"]
    await common_show_zip(c, game_id, manager)


async def common_show_zip(c: CallbackQuery, game_id: int, manager: DialogManager):
    player: dto.Player = manager.middleware_data["player"]
    dao: HolderDao = manager.middleware_data["dao"]
    dcf: Factory = manager.middleware_data["dcf"]
    file_gateway: FileGateway = manager.middleware_data["file_gateway"]
    game_ = await game.get_game_package(game_id, player, dao.game_packager, dcf, file_gateway)
    zip_ = pack_scn(game_)
    await c.message.answer_document(BufferedInputFile(file=zip_.read(), filename="scenario.zip"))


async def rename_game_handler(m: Message, dialog: Any, dialog_manager: DialogManager):
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    player: dto.Player = dialog_manager.middleware_data["player"]
    game_ = await get_game(dialog_manager.dialog_data["my_game_id"], dao=dao.game)
    await rename_game(player, game_, m.text.strip(), dao.game)


async def start_waivers(c: CallbackQuery, widget: Button, manager: DialogManager):
    await c.answer()
    player: dto.Player = manager.middleware_data["player"]
    dao: HolderDao = manager.middleware_data["dao"]
    game_ = await game.get_game(
        id_=int(manager.dialog_data["my_game_id"]),
        author=player,
        dao=dao.game,
    )
    await game.start_waivers(game_, player, dao.game)


async def select_date(c: CallbackQuery, widget, manager: DialogManager, selected_date: date):
    await c.answer()
    data = manager.dialog_data
    if not isinstance(data, dict):
        data = {}
    data["scheduled_date"] = selected_date.isoformat()
    await manager.switch_to(states.GameScheduleSG.time)


async def process_time_message(m: Message, dialog_: Any, manager: DialogManager) -> None:
    try:
        time_ = datetime.strptime(m.text, TIME_FORMAT).time()
    except ValueError:
        await m.answer("Некорректный формат времени. Пожалуйста введите время в формате ЧЧ:ММ")
        return
    data = manager.dialog_data
    data["scheduled_time"] = time_.isoformat()
    await manager.switch_to(states.GameScheduleSG.confirm)


async def schedule_game(c: CallbackQuery, widget: Button, manager: DialogManager):
    at = datetime.combine(
        date=date.fromisoformat(manager.dialog_data["scheduled_date"]),
        time=time.fromisoformat(manager.dialog_data["scheduled_time"]),
        tzinfo=tz_game,
    )
    game_id = int(manager.start_data["my_game_id"])
    player: dto.Player = manager.middleware_data["player"]
    dao: HolderDao = manager.middleware_data["dao"]
    scheduler: Scheduler = manager.middleware_data["infrastructure.scheduler"]
    await game.plain_start(
        game=await dao.game.get_by_id(game_id, player),
        author=player,
        start_at=at,
        dao=dao.game,
        scheduler=scheduler,
    )
    await c.answer("Запланировано успешно")
    await manager.done()


async def show_game_orgs(c: CallbackQuery, widget: Button, manager: DialogManager):
    await c.answer()
    game_id = manager.dialog_data["game_id"]
    await manager.start(states.GameOrgsSG.orgs_list, data={"game_id": game_id, "completed": True})


async def show_my_game_orgs(c: CallbackQuery, widget: Button, manager: DialogManager):
    await c.answer()
    game_id = manager.dialog_data["my_game_id"]
    await manager.start(states.GameOrgsSG.orgs_list, data={"game_id": game_id})


async def publish_game(c: CallbackQuery, widget: Button, manager: DialogManager):
    await c.answer()
    game_id = manager.dialog_data["my_game_id"]
    await manager.start(states.GamePublishSG.prepare, data={"game_id": game_id})


async def get_excel_results_handler(c: CallbackQuery, widget: Button, manager: DialogManager):
    game_id = manager.dialog_data["game_id"]
    dao: HolderDao = manager.middleware_data["dao"]
    author: dto.Player = manager.middleware_data["player"]
    full_game = await get_full_game(id_=game_id, author=author, dao=dao.game)
    game_stat = await get_game_stat(game=full_game, player=author, dao=dao.game_stat)
    file = BytesIO()
    export_results(game=full_game, game_stat=game_stat, file=file)
    file.seek(0)
    await c.message.answer_document(
        document=BufferedInputFile(file=file.read(), filename=f"{full_game.name}.xlsx"),
    )
    file.close()
