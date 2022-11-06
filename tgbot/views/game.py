import logging
from dataclasses import dataclass
from typing import Iterable

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.utils.markdown import html_decoration as hd

from db.dao.holder import HolderDao
from shvatka.clients.file_storage import FileStorage
from shvatka.dal.game_play import GamePreparer
from shvatka.models import dto
from shvatka.models.dto.scn.time_hint import TimeHint
from shvatka.views.game import GameViewPreparer, GameView, GameLogWriter, OrgNotifier
from tgbot.views.hint_factory.hint_content_resolver import HintContentResolver
from tgbot.views.hint_sender import HintSender

logger = logging.getLogger(__name__)


@dataclass
class BotView(GameViewPreparer, GameView):
    bot: Bot
    hint_sender: HintSender

    async def prepare_game_view(
        self, game: dto.Game, teams: Iterable[dto.Team], orgs: Iterable[dto.Organizer], dao: GamePreparer,
    ) -> None:
        # TODO set bot commands for orgs, hide bot commands for players
        for team in teams:
            try:
                await self.bot.edit_message_reply_markup(
                    chat_id=team.chat.tg_id,
                    message_id=await dao.get_poll_msg(team=team, game=game),
                    reply_markup=None,
                )
            except TelegramAPIError as e:
                logger.error("can't remove waivers keyboard for team %s", team.id, exc_info=e)


    async def send_puzzle(self, team: dto.Team, puzzle: TimeHint, level: dto.Level) -> None:
        await self.hint_sender.send_hints(
            chat_id=team.chat.tg_id,
            hint_containers=puzzle.hint,
            caption=hd.bold(f"Уровень № {level.number_in_game + 1}")
        )

    async def send_hint(self, team: dto.Team, hint_number: int, level: dto.Level) -> None:
        hint = level.get_hint(hint_number)
        if level.is_last_hint(hint_number):
            hint_caption = f"Последняя подсказка уровня №{level.number_in_game + 1} ({hint.time} мин.):\n"
        else:
            hint_caption = f"Уровень №{level.number_in_game + 1}. Подсказка ({hint.time} мин.):\n"
        await self.hint_sender.send_hints(
            chat_id=team.chat.tg_id,
            hint_containers=hint.hint,
            caption=hint_caption
        )

    async def duplicate_key(self, key: dto.KeyTime) -> None:
        await self.bot.send_message(chat_id=key.team.chat.tg_id, text=f"Ключ {hd.pre(key.text)} уже был введён ранее.")

    async def correct_key(self, key: dto.KeyTime) -> None:
        await self.bot.send_message(chat_id=key.team.chat.tg_id, text=f"Ключ {hd.pre(key.text)} верный! Поздравляю!")

    async def wrong_key(self, key: dto.KeyTime) -> None:
        await self.bot.send_message(chat_id=key.team.chat.tg_id, text=f"Ключ {hd.pre(key.text)} неверный.")

    async def game_finished(self, team: dto.Team) -> None:
        await self.bot.send_message(chat_id=team.chat.tg_id, text=f"Игра завершена! Поздравляю!")

    async def game_finished_by_all(self, team: dto.Team) -> None:
        """todo change bot commands"""
        pass


@dataclass
class GameBotLog(GameLogWriter):
    bot: Bot
    log_chat_id: int

    async def log(self, message: str) -> None:
        await self.bot.send_message(chat_id=self.log_chat_id, text=message)


@dataclass
class BotOrgNotifier(OrgNotifier):
    bot: Bot

    async def notify(self, event) -> None:
        pass


def create_bot_game_view(bot: Bot, dao: HolderDao, storage: FileStorage) -> BotView:
    return BotView(
        bot=bot,
        hint_sender=HintSender(
            bot=bot,
            resolver=HintContentResolver(dao=dao.file_info, file_storage=storage),
        ),
    )
