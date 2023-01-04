from typing import Iterable

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from shvatka.models import dto
from shvatka.models.enums.played import Played


class WaiverVoteCD(CallbackData, prefix="waiver_vote"):
    vote: Played
    team_id: int


class WaiverConfirmCD(CallbackData, prefix="confirm_waivers"):
    game_id: int
    team_id: int


class WaiverManagePlayerCD(CallbackData, prefix="waiver_player"):
    game_id: int
    team_id: int
    player_id: int


class WaiverMainCD(CallbackData, prefix="waiver_main"):
    game_id: int
    team_id: int


class WaiverRemovePlayerCD(CallbackData, prefix="waiver_remove_player"):
    game_id: int
    team_id: int
    player_id: int


class WaiverAddForceMenuCD(CallbackData, prefix="waiver_add_force"):
    game_id: int
    team_id: int


class WaiverAddPlayerForceCD(CallbackData, prefix="waiver_add_force"):
    game_id: int
    team_id: int
    player_id: int


def get_kb_waivers(team: dto.Team) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Играю", callback_data=WaiverVoteCD(vote=Played.yes, team_id=team.id))
    builder.button(text="Не могу", callback_data=WaiverVoteCD(vote=Played.no, team_id=team.id))
    builder.button(text="Думаю", callback_data=WaiverVoteCD(vote=Played.think, team_id=team.id))
    builder.adjust(3)
    return builder.as_markup()


def get_kb_manage_waivers(
    team: dto.Team, players: Iterable[dto.Player], game: dto.Game
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Подтвердить вейверы", callback_data=WaiverConfirmCD(game_id=game.id, team_id=team.id)
    )
    builder.button(
        text="Добавить игрока принудительно",
        callback_data=WaiverAddForceMenuCD(game_id=game.id, team_id=team.id),
    )
    for player in players:
        builder.button(
            text=player.user.name_mention,
            callback_data=WaiverManagePlayerCD(
                game_id=game.id, team_id=team.id, player_id=player.id
            ),
        )
    builder.adjust(1)
    return builder.as_markup()


def get_kb_waiver_one_player(
    team: dto.Team, player: dto.Player, game: dto.Game
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="К списку игроков", callback_data=WaiverMainCD(game_id=game.id, team_id=team.id)
    )
    builder.button(
        text="Исключить из вейверов",
        callback_data=WaiverRemovePlayerCD(
            game_id=game.id,
            team_id=team.id,
            player_id=player.id,
        ),
    )
    builder.adjust(1)
    return builder.as_markup()


def get_kb_force_add_waivers(
    team: dto.Team, players: Iterable[dto.Player], game: dto.Game
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="К списку игроков", callback_data=WaiverMainCD(game_id=game.id, team_id=team.id)
    )
    for player in players:
        builder.button(
            text=player.user.name_mention,
            callback_data=WaiverAddPlayerForceCD(
                game_id=game.id,
                team_id=team.id,
                player_id=player.id,
            ),
        )
    builder.adjust(1)
    return builder.as_markup()
