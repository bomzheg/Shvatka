from collections.abc import Iterator
from dataclasses import dataclass

from shvatka.core.models import dto
from shvatka.core.models.dto import hints
from shvatka.core.search.adapters import GlobalSearchDao
from shvatka.core.search.dto import (
    GameHit,
    LevelHit,
    LevelMatchField,
    LevelWithGame,
    PlayerHit,
    PlayerMatchField,
    SearchFilters,
    SearchResults,
    TeamHit,
)

SNIPPET_RADIUS = 40


def make_snippet(text: str, query: str, radius: int = SNIPPET_RADIUS) -> str | None:
    """Кусочек текста вокруг найденного вхождения (без учёта регистра) или None."""
    index = text.lower().find(query.lower())
    if index < 0:
        return None
    start = max(0, index - radius)
    end = min(len(text), index + len(query) + radius)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return prefix + text[start:end] + suffix


def iter_hint_texts(hint: hints.AnyHint) -> Iterator[str]:
    """Все текстовые поля подсказки, в которых имеет смысл искать."""
    if isinstance(hint, hints.TextHint):
        yield hint.text
    elif isinstance(hint, hints.VenueHint):
        yield hint.title
        yield hint.address
    elif isinstance(hint, hints.ContactHint):
        yield hint.first_name
        if hint.last_name:
            yield hint.last_name
        yield hint.phone_number
    if isinstance(hint, hints.CaptionMixin) and hint.caption:
        yield hint.caption


def find_level_hits(candidate: LevelWithGame, query: str) -> list[LevelHit]:
    """Точные места совпадений внутри уровня: name_id и текстовые части подсказок."""
    result: list[LevelHit] = []
    level = candidate.level
    if snippet := make_snippet(level.name_id, query):
        result.append(
            LevelHit(
                level=level,
                game=candidate.game,
                found_in=LevelMatchField.name_id,
                snippet=snippet,
            )
        )
    for hint_number, time_hint in enumerate(level.scenario.time_hints):
        for part_number, hint_part in enumerate(time_hint.hint):
            for text in iter_hint_texts(hint_part):
                if snippet := make_snippet(text, query):
                    result.append(
                        LevelHit(
                            level=level,
                            game=candidate.game,
                            found_in=LevelMatchField.hint,
                            hint_number=hint_number,
                            hint_time=time_hint.time,
                            hint_part_number=part_number,
                            snippet=snippet,
                        )
                    )
                    break
    return result


def classify_player_hit(player: dto.Player, query: str) -> PlayerHit | None:
    if player.username and (snippet := make_snippet(player.username, query)):
        return PlayerHit(player=player, found_in=PlayerMatchField.username, snippet=snippet)
    tg_username = player.get_tg_username()
    if tg_username and (snippet := make_snippet(tg_username, query)):
        return PlayerHit(player=player, found_in=PlayerMatchField.tg_username, snippet=snippet)
    tg_name = player.get_tg_fullname()
    if tg_name and (snippet := make_snippet(tg_name, query)):
        return PlayerHit(player=player, found_in=PlayerMatchField.tg_name, snippet=snippet)
    forum_name = player.get_forum_name()
    if forum_name and (snippet := make_snippet(forum_name, query)):
        return PlayerHit(player=player, found_in=PlayerMatchField.forum_name, snippet=snippet)
    return None


@dataclass(kw_only=True, slots=True, frozen=True)
class GlobalSearchInteractor:
    dao: GlobalSearchDao

    async def __call__(self, *, query: str, filters: SearchFilters | None = None) -> SearchResults:
        if filters is None:
            filters = SearchFilters()
        query = query.strip()
        if not query:
            return SearchResults()
        games: list[GameHit] = []
        levels: list[LevelHit] = []
        teams: list[TeamHit] = []
        players: list[PlayerHit] = []
        if filters.games:
            games = [
                GameHit(game=game, snippet=make_snippet(game.name, query) or game.name)
                for game in await self.dao.search_completed_games(query)
            ]
        if filters.levels:
            for candidate in await self.dao.search_levels_of_completed_games(query):
                levels.extend(find_level_hits(candidate, query))
        if filters.teams:
            teams = [
                TeamHit(team=team, snippet=make_snippet(team.name, query) or team.name)
                for team in await self.dao.search_teams(query)
            ]
        if filters.players:
            players = [
                hit
                for player in await self.dao.search_players(query)
                if (hit := classify_player_hit(player, query))
            ]
        return SearchResults(games=games, levels=levels, teams=teams, players=players)
