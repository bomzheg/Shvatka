from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Format

from tgbot.states import LevelSG
from .getters import get_time_hints, get_level_id
from .handlers import process_result, start_add_time_hint, process_id, process_keys, save_level

level = Dialog(
    Window(
        Const(
            "<b>ID уровня</b>\n\n"
            "Для начала дай уровню короткое описание (ID) (цифры, латинские буквы). "
            "Оно будет использовано в дальнейшем при создании игры, "
            "для указания очередности уровней.\n"
            "\n"
            "Внимание! ID и название файла не должны содержать "
            "конфиденциальной информации, дающих представление о "
            "ключах, локациях и другой существенной информации "
            "поскольку ID и название файла попадают в лог-файлы, предназначенные "
            "для чтения системным администратором"
        ),
        MessageInput(func=process_id),
        state=LevelSG.level_id,
    ),
    Window(
        Format("Уровень <b>{level_id}</b>\n\n"),
        Const(
            "<b>Ключи уровня<b/>\n\n"
            "Отлично, перейдём к ключам. Ключи принимаются в следующих форматах: "
            "<code>SHENGLISHLETTERSANDDIDGITS СХРУССКИЕБУКВЫИЦИФРЫ</code>.\n"
            "Если требуется указать несколько ключей напишите каждый с новой строки."
        ),
        MessageInput(func=process_keys),
        state=LevelSG.keys,
        getter=get_level_id,
    ),
    Window(
        Format("Подсказки уровня{level_id}:\n"),
        Format("{rendered}"),
        Button(Const("Добавить подсказку"), id="add_time_hint", on_click=start_add_time_hint),
        Button(
            Const("Готово, сохранить"),
            id="save",
            on_click=save_level,
            when=lambda d, **_: len(d["time_hints"]) > 1,
        ),
        state=LevelSG.time_hints,
        getter=get_time_hints,
    ),
    on_process_result=process_result,
)
