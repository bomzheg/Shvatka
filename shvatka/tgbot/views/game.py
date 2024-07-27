from datetime import datetime
import json
import logging
from contextlib import suppress
from dataclasses import dataclass
from typing import Iterable, cast

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.utils.markdown import html_decoration as hd
from dataclass_factory import Factory

from shvatka.core.interfaces.dal.game_play import GamePreparer
from shvatka.core.models import dto, enums
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.views.game import (
    GameViewPreparer,
    GameView,
    GameLogWriter,
    OrgNotifier,
    Event,
    LevelUp,
    NewOrg,
    LevelTestCompleted,
    GameLogEvent,
    GameLogType,
)
from shvatka.tgbot.views.bot_alert import BotAlert
from shvatka.tgbot.views.hint_sender import HintSender
from shvatka.tgbot.views.keys import KeyEmoji

PREPARE_GAME_TEMPLATE = (
    "Игра {game_name} начнётся через {second_left} сек. \n"
    "Ваша команда {team_name} будет получать уровни и подсказки прямо тут.\n"
    "Ключи так же вводите прямо сюда. Один ключ - одно сообщение. "
    "Формат ключей SHСЛОВО или СХСЛОВО. Все буквы обязательно большими. Удачи!"
)

logger = logging.getLogger(__name__)


@dataclass
class BotView(GameViewPreparer, GameView):
    bot: Bot
    hint_sender: HintSender
    bot_alert: BotAlert

    async def prepare_game_view(
        self,
        game: dto.Game,
        teams: Iterable[dto.Team],
        orgs: Iterable[dto.Organizer],
        dao: GamePreparer,
    ) -> None:
        # TODO set bot commands for orgs, hide bot commands for players
        for team in teams:
            try:
                await self.bot.edit_message_reply_markup(
                    chat_id=team.get_chat_id(),
                    message_id=await dao.get_poll_msg(team=team, game=game),
                    reply_markup=None,
                )
            except TelegramAPIError as e:
                logger.warning("can't remove waivers keyboard for team %s", team.id, exc_info=e)
            try:
                if not game.start_at:
                    await self.bot_alert.alert(f"Not set up game.start_at for game_id={game.id}")
                    logger.error("not set up game.start_at", extra=dict(game_id=game.id))
                    raise RuntimeError("not set up game.start_at")
                await self.bot.send_message(
                    chat_id=team.get_chat_id(),
                    text=PREPARE_GAME_TEMPLATE.format(
                        game_name=hd.quote(game.name),
                        second_left=(game.start_at - datetime.now(tz_utc)).seconds,
                        team_name=hd.quote(team.name),
                    ),
                )
            except TelegramAPIError as e:
                logger.exception(
                    "can't send prepare message to team",
                    exc_info=e,
                    extra=dict(team_id=team.id, chat_id=team.get_chat_id()),
                )
                await self.bot_alert.alert(
                    f"can't send prepare message to team {team.id} [{e.__class__.__name__}]"
                )

    async def send_puzzle(self, team: dto.Team, level: dto.Level) -> None:
        assert level.number_in_game is not None
        await self.hint_sender.send_hints(
            chat_id=team.get_chat_id(),
            hint_containers=level.get_hint(0).hint,
            caption=hd.bold(f"Уровень № {level.number_in_game + 1}"),
        )

    async def send_hint(self, team: dto.Team, hint_number: int, level: dto.Level) -> None:
        assert level.number_in_game is not None
        hint = level.get_hint(hint_number)
        if level.is_last_hint(hint_number):
            hint_caption = (
                f"Последняя подсказка уровня №{level.number_in_game + 1} ({hint.time} мин.):\n"
            )
        else:
            hint_caption = f"Уровень №{level.number_in_game + 1}. Подсказка ({hint.time} мин.):\n"
        await self.hint_sender.send_hints(
            chat_id=team.get_chat_id(), hint_containers=hint.hint, caption=hint_caption
        )

    async def duplicate_key(self, key: dto.KeyTime) -> None:
        await self.bot.send_message(
            chat_id=key.team.get_chat_id(),
            text=(
                f"{KeyEmoji.duplicate.value}Ключ {hd.code(key.text)} "
                f"({'не' if key.type_ == enums.KeyType.wrong else ''}верный) уже был введён ранее."
            ),
        )

    async def correct_key(self, key: dto.KeyTime) -> None:
        await self.bot.send_message(
            chat_id=key.team.get_chat_id(),
            text=f"{KeyEmoji.correct.value}Ключ {hd.code(key.text)} верный! Поздравляю!",
        )

    async def wrong_key(self, key: dto.KeyTime) -> None:
        await self.bot.send_message(
            chat_id=key.team.get_chat_id(),
            text=f"{KeyEmoji.incorrect.value}Ключ {hd.code(key.text)} неверный.",
        )

    async def bonus_key(self, key: dto.KeyTime, bonus: float) -> None:
        if bonus >= 0:
            text = (
                f"{KeyEmoji.bonus.value}Бонусный ключ {hd.code(key.text)}.\n"
                f"Бонус: {bonus:.2f} мин."
            )
        else:
            text = (
                f"{KeyEmoji.bonus.value}Штрафной ключ {hd.code(key.text)}.\n"
                f"Штраф: {bonus:.2f} мин."
            )
        await self.bot.send_message(
            chat_id=key.team.get_chat_id(),
            text=text,
        )

    async def game_finished(self, team: dto.Team) -> None:
        await self.bot.send_message(chat_id=team.get_chat_id(), text="Игра завершена! Поздравляю!")

    async def game_finished_by_all(self, team: dto.Team) -> None:
        """todo change bot commands"""
        pass


@dataclass
class GameBotLog(GameLogWriter):
    bot: Bot
    log_chat_id: int

    async def log(self, event_log: GameLogEvent) -> None:
        match event_log:
            case GameLogEvent(GameLogType.GAME_WAIVERS_STARTED):
                text = "Начался сбор вейверов на игру {game}"
            case GameLogEvent(GameLogType.GAME_PLANED):
                text = "Начало игры {game} запланировано на {at}"
            case GameLogEvent(GameLogType.GAME_STARTED):
                text = "Игра {game} началась"
            case GameLogEvent(GameLogType.GAME_FINISHED):
                text = "Игра {game} завершена"
            case GameLogEvent(GameLogType.TEAMS_MERGED):
                text = (
                    "Капитан {captain} объединил "
                    "свою команду {primary_team} с форумной {secondary_team}"
                )
            case GameLogEvent(GameLogType.PLAYERS_MERGED):
                text = "Игрок в боте {primary} объединён с форумным {secondary}"
            case GameLogEvent(GameLogType.TEAM_CREATED):
                text = "Создана команда {team}. Капитан: {captain}"
            case _:
                raise ValueError
        data = {k: hd.quote(v) for k, v in event_log.data.items()}
        await self.bot.send_message(chat_id=self.log_chat_id, text=text.format_map(data))


@dataclass
class BotOrgNotifier(OrgNotifier):
    bot: Bot
    dcf = Factory()

    async def notify(self, event: Event) -> None:
        match event:
            case LevelUp():
                for org in event.orgs_list:
                    if org.player.get_chat_id() is None:
                        logger.warning("player %s have no user chat_id", org.player)
                        continue
                    with suppress(TelegramAPIError):
                        await self.notify_level_up(cast(LevelUp, event), org)
            case NewOrg():
                for org in event.orgs_list:
                    if org.player.get_chat_id() is None:
                        logger.warning("player %s have no user chat_id", org.player)
                        continue
                    with suppress(TelegramAPIError):
                        await self.notify_new_org(cast(NewOrg, event), org)
            case LevelTestCompleted():
                for org in event.orgs_list:
                    if org.player.get_chat_id() is None:
                        logger.warning("player %s have no user chat_id", org.player)
                        continue
                    with suppress(TelegramAPIError):
                        await self.level_test_completed(cast(LevelTestCompleted, event), org)

    async def notify_level_up(self, level_up: LevelUp, org: dto.Organizer):
        assert level_up.new_level.number_in_game is not None
        await self.bot.send_message(
            chat_id=org.player.get_chat_id(),
            text=f"Команда {hd.quote(level_up.team.name)} перешла "
            f"на уровень {level_up.new_level.number_in_game + 1} "
            f"({level_up.new_level.name_id})",
        )

    async def notify_new_org(self, new_org: NewOrg, org: dto.Organizer):
        await self.bot.send_message(
            chat_id=org.player.get_chat_id(),
            text=f"На игру {hd.quote(new_org.game.name)} "
            f"добавлен новый орг {hd.quote(new_org.org.player.name_mention)}",
        )

    async def level_test_completed(self, event: LevelTestCompleted, org: dto.Organizer):
        results = json.dumps(self.dcf.dump(event.result.full_data), ensure_ascii=False)[:3000]
        await self.bot.send_message(
            chat_id=org.player.get_chat_id(),
            text=f"Тестирование уровня {event.suite.level.name_id}.\n"
            f"Игрок {hd.quote(event.suite.tester.player.name_mention)} "
            f"закончил тестирование уровня за {event.result.td.seconds // 60} минут "
            f"{event.result.td.seconds % 60} c.\n"
            f"{hd.pre(hd.quote(results))}",
        )
