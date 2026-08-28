import typing
from collections.abc import Sequence
from dataclasses import dataclass

from shvatka.api.shared.responses import Page
from shvatka.core.search import dto as search_dto


@dataclass(kw_only=True, frozen=True, slots=True)
class GameSearchResult:
    game_id: int
    game_name: str
    game_number: int | None
    snippet: str
    type: typing.Literal["game"] = "game"

    @classmethod
    def from_core(cls, hit: search_dto.GameHit) -> "GameSearchResult":
        return cls(
            game_id=hit.game.id,
            game_name=hit.game.name,
            game_number=hit.game.number,
            snippet=hit.snippet,
        )


@dataclass(kw_only=True, frozen=True, slots=True)
class LevelSearchResult:
    level_id: int
    level_name_id: str
    level_number: int | None
    game_id: int
    game_name: str
    game_number: int | None
    found_in: typing.Literal["name_id", "hint", "key"]
    hint_number: int | None
    hint_time: int | None
    hint_part_number: int | None
    condition_key: Sequence[str] = ()
    condition_timer: int | None = None
    key: str | None = None
    snippet: str
    type: typing.Literal["level"] = "level"

    @classmethod
    def from_core(cls, hit: search_dto.LevelHit) -> "LevelSearchResult":
        return cls(
            level_id=hit.level.db_id,
            level_name_id=hit.level.name_id,
            level_number=hit.level.number_in_game,
            game_id=hit.game.id,
            game_name=hit.game.name,
            game_number=hit.game.number,
            found_in=typing.cast(typing.Literal["name_id", "hint", "key"], hit.found_in.value),
            hint_number=hit.hint_number,
            hint_time=hit.hint_time,
            hint_part_number=hit.hint_part_number,
            condition_key=hit.condition_key,
            condition_timer=hit.condition_timer,
            key=hit.key,
            snippet=hit.snippet,
        )


@dataclass(kw_only=True, frozen=True, slots=True)
class TeamSearchResult:
    team_id: int
    team_name: str
    snippet: str
    type: typing.Literal["team"] = "team"

    @classmethod
    def from_core(cls, hit: search_dto.TeamHit) -> "TeamSearchResult":
        return cls(team_id=hit.team.id, team_name=hit.team.name, snippet=hit.snippet)


@dataclass(kw_only=True, frozen=True, slots=True)
class PlayerSearchResult:
    player_id: int
    player_name: str
    found_in: typing.Literal["username", "tg_username", "tg_name", "forum_name"]
    snippet: str
    type: typing.Literal["player"] = "player"

    @classmethod
    def from_core(cls, hit: search_dto.PlayerHit) -> "PlayerSearchResult":
        return cls(
            player_id=hit.player.id,
            player_name=hit.player.name_mention,
            found_in=typing.cast(
                typing.Literal["username", "tg_username", "tg_name", "forum_name"],
                hit.found_in.value,
            ),
            snippet=hit.snippet,
        )


SearchResult: typing.TypeAlias = (
    GameSearchResult | LevelSearchResult | TeamSearchResult | PlayerSearchResult
)


def search_results_to_page(results: search_dto.SearchResults) -> Page[SearchResult]:
    content: list[SearchResult] = []
    content.extend(GameSearchResult.from_core(hit) for hit in results.games)
    content.extend(LevelSearchResult.from_core(hit) for hit in results.levels)
    content.extend(TeamSearchResult.from_core(hit) for hit in results.teams)
    content.extend(PlayerSearchResult.from_core(hit) for hit in results.players)
    return Page(content)
