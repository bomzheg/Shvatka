from datetime import date, datetime, time
from io import BytesIO
from typing import Any

from aiogram.types import BufferedInputFile, CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.games.editor_interactors import (
    ChangeGameStatusInteractor,
    ExportGameZipInteractor,
    PlanGameStartInteractor,
)
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.interfaces.nursery import Nursery
from shvatka.core.models import enums
from shvatka.core.scenario.interactors import (
    AllGameKeysPrintInteractor,
    AllGameKeysReaderInteractor,
    GameScenarioTransitionsInteractor,
)
from shvatka.core.services.game import get_full_game, get_game, rename_game
from shvatka.core.services.game_stat import get_game_stat
from shvatka.core.utils.datetime_utils import TIME_FORMAT, tz_game
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.printer.results import export_results
from shvatka.tgbot import states
from shvatka.tgbot.tasks import publish_scenario_to_forum
from shvatka.tgbot.views.results.rich import ResultsRichSender


async def select_my_game(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    data = manager.dialog_data
    if not isinstance(data, dict):
        data = {}
    data["my_game_id"] = int(item_id)
    await manager.switch_to(states.MyGamesPanelSG.game_menu)


async def select_game(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    data = manager.dialog_data
    if not isinstance(data, dict):
        data = {}
    data["game_id"] = int(item_id)
    await manager.switch_to(states.CompletedGamesPanelSG.game)


async def start_schedule_game(c: CallbackQuery, widget: Button, manager: DialogManager):
    game_id = manager.dialog_data["my_game_id"]
    await manager.start(states.GameScheduleSG.date, data={"my_game_id": int(game_id)})


@inject
async def cancel_scheduled_game(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    interactor: FromDishka[PlanGameStartInteractor],
    identity: FromDishka[IdentityProvider],
):
    game_id = manager.dialog_data["my_game_id"]
    await interactor(game_id=game_id, start_at=None, identity=identity)


async def show_scn(c: CallbackQuery, widget: Button, manager: DialogManager):
    game_id = manager.dialog_data["my_game_id"]
    await manager.start(states.GameEditSG.current_levels, data={"game_id": int(game_id)})


@inject
async def show_zip_scn(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    interactor: FromDishka[ExportGameZipInteractor],
):
    zip_ = await interactor(game_id=manager.dialog_data["game_id"], identity=identity)
    assert isinstance(c.message, Message)
    await c.message.answer_document(BufferedInputFile(file=zip_.read(), filename="scenario.zip"))


@inject
async def show_my_zip_scn(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    interactor: FromDishka[ExportGameZipInteractor],
):
    zip_ = await interactor(game_id=manager.dialog_data["my_game_id"], identity=identity)
    assert isinstance(c.message, Message)
    await c.message.answer_document(BufferedInputFile(file=zip_.read(), filename="scenario.zip"))


@inject
async def show_all_keys(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    interactor: FromDishka[AllGameKeysReaderInteractor],
    identity: FromDishka[IdentityProvider],
):
    assert isinstance(c.message, Message)
    await c.message.answer_document(
        document=BufferedInputFile(
            file=(await interactor(manager.dialog_data["my_game_id"], identity)).read(),
            filename="all_keys.xlsx",
        )
    )


@inject
async def show_all_keys_to_print(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    interactor: FromDishka[AllGameKeysPrintInteractor],
    identity: FromDishka[IdentityProvider],
):
    assert isinstance(c.message, Message)
    await c.message.answer_document(
        document=BufferedInputFile(
            file=(await interactor(manager.dialog_data["my_game_id"], identity)).read(),
            filename="keys_to_print.pdf",
        )
    )


@inject
async def show_transitions(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    interactor: FromDishka[GameScenarioTransitionsInteractor],
    identity: FromDishka[IdentityProvider],
):
    assert isinstance(c.message, Message)
    game_id: int | None = manager.dialog_data.get(
        "game_id", manager.dialog_data.get("my_game_id", None)
    )
    assert game_id is not None
    await c.message.answer_document(
        document=BufferedInputFile(
            file=(await interactor(game_id, identity)).read(),
            filename="transitions.png",
        )
    )


@inject
async def rename_game_handler(
    m: Message,
    dialog: Any,
    dialog_manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    dao: FromDishka[HolderDao],
):
    player = await identity.get_required_player()
    game_ = await get_game(dialog_manager.dialog_data["my_game_id"], dao=dao.game)
    assert m.text
    await rename_game(player, game_, m.text.strip(), dao.game)


@inject
async def start_waivers(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    interactor: FromDishka[ChangeGameStatusInteractor],
    identity: FromDishka[IdentityProvider],
):
    game_id = int(manager.dialog_data["my_game_id"])
    await interactor(game_id=game_id, identity=identity, status=enums.GameStatus.getting_waivers)


async def select_date(c: CallbackQuery, widget, manager: DialogManager, selected_date: date):
    data = manager.dialog_data
    if not isinstance(data, dict):
        data = {}
    data["scheduled_date"] = selected_date.isoformat()
    await manager.switch_to(states.GameScheduleSG.time)


async def process_time_message(m: Message, dialog_: Any, manager: DialogManager) -> None:
    assert m.text
    try:
        time_ = datetime.strptime(m.text, TIME_FORMAT).time()  # noqa: DTZ007
    except ValueError:
        await m.answer("Некорректный формат времени. Пожалуйста введите время в формате ЧЧ:ММ")
        return
    data = manager.dialog_data
    data["scheduled_time"] = time_.isoformat()
    await manager.switch_to(states.GameScheduleSG.confirm)


@inject
async def schedule_game(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    interactor: FromDishka[PlanGameStartInteractor],
    identity: FromDishka[IdentityProvider],
):
    at = datetime.combine(
        date=date.fromisoformat(manager.dialog_data["scheduled_date"]),
        time=time.fromisoformat(manager.dialog_data["scheduled_time"]),
        tzinfo=tz_game,
    )
    data: dict[str, Any] = manager.start_data  # type: ignore[assignment]
    game_id = int(data["my_game_id"])
    await interactor(game_id=game_id, start_at=at, identity=identity)
    await c.answer("Запланировано успешно")
    await manager.done()


async def show_game_orgs(c: CallbackQuery, widget: Button, manager: DialogManager):
    game_id = manager.dialog_data["game_id"]
    await manager.start(states.GameOrgsSG.orgs_list, data={"game_id": game_id, "completed": True})


async def show_my_game_orgs(c: CallbackQuery, widget: Button, manager: DialogManager):
    game_id = manager.dialog_data["my_game_id"]
    await manager.start(states.GameOrgsSG.orgs_list, data={"game_id": game_id})


async def show_game_release(c: CallbackQuery, widget: Button, manager: DialogManager):
    game_id = manager.dialog_data["my_game_id"]
    await manager.start(states.GameReleaseSG.menu, data={"game_id": int(game_id)})


async def publish_game(c: CallbackQuery, widget: Button, manager: DialogManager):
    game_id = manager.dialog_data["my_game_id"]
    await manager.start(states.GamePublishSG.prepare, data={"game_id": game_id})


async def to_publish_game_forum(c: CallbackQuery, widget: Button, manager: DialogManager):
    game_id = manager.dialog_data["my_game_id"]
    await manager.start(states.GamePublishSG.forum, data={"game_id": game_id})


@inject
async def publish_game_forum(
    m: Message,
    widget: Any,
    manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    dao: FromDishka[HolderDao],
    nursery: FromDishka[Nursery],
):
    assert m.text
    username, password = map(str.strip, m.text.split("\n", maxsplit=1))
    game_id = manager.dialog_data["my_game_id"]
    game_ = await get_full_game(game_id, identity, dao.game)
    nursery.spawn(
        publish_scenario_to_forum,
        game=game_,
        username=username,
        password=password,
        chat_id=m.chat.id,
    )


@inject
async def show_results(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    dao: FromDishka[HolderDao],
    results_sender: FromDishka[ResultsRichSender],
):
    """Post the results as a rich message and open the window of what else can be done."""
    game_id = manager.dialog_data["game_id"]
    full_game = await get_full_game(id_=game_id, identity=identity, dao=dao.game)
    game_stat = await get_game_stat(game=full_game, identity=identity, dao=dao.game_stat)
    assert isinstance(c.message, Message)
    await results_sender.send_results(
        chat_id=c.message.chat.id,
        game=full_game,
        game_stat=game_stat,
    )
    await manager.switch_to(states.CompletedGamesPanelSG.results)


@inject
async def get_excel_results_handler(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    dao: FromDishka[HolderDao],
):
    game_id = manager.dialog_data["game_id"]
    full_game = await get_full_game(id_=game_id, identity=identity, dao=dao.game)
    game_stat = await get_game_stat(game=full_game, identity=identity, dao=dao.game_stat)
    file = BytesIO()
    export_results(game=full_game, game_stat=game_stat, file=file)
    file.seek(0)
    assert isinstance(c.message, Message)
    await c.message.answer_document(
        document=BufferedInputFile(file=file.read(), filename=f"{full_game.name}.xlsx"),
    )
    file.close()


@inject
async def complete_game_handler(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    interactor: FromDishka[ChangeGameStatusInteractor],
    identity: FromDishka[IdentityProvider],
):
    game_id = manager.dialog_data["my_game_id"]
    await interactor(game_id=game_id, status=enums.GameStatus.complete, identity=identity)
    await manager.done()
