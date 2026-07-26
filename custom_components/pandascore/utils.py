"""Utility functions for Pandascore integration."""

from datetime import datetime, timedelta
from functools import partial
from typing import Any, Literal

from babel.dates import format_timedelta
from homeassistant.core import HomeAssistant
from homeassistant.util.dt import now

from custom_components.pandascore.models import Match, Opponent, Result

LOCALE_MAP = {
    "fr": "fr_FR",
    "en": "en_US",
    "de": "de_DE",
    "es": "es_ES",
}


def estimate_duration_ms(videogame_id: int, number_of_games: int) -> int:
    """TODO"""
    # durations in milliseconds per single game
    mapping = {
        1: 60 * 60 * 1000,
        3: 50 * 60 * 1000,
        22: 10 * 60 * 1000,
        23: 30 * 60 * 1000,
        26: 50 * 60 * 1000,
    }
    per = mapping.get(videogame_id, 60 * 60 * 1000)
    return per * max(1, number_of_games)


def build_match_entry(
    team_id: int, match: Match, include_result: bool = False
) -> dict[str, Any]:
    """TODO"""
    scheduled = match.scheduled_at or match.begin_at
    end_at = match.end_at
    if scheduled and not end_at:
        videogame_id = int(match.videogame.id or 0)
        number_of_games = int(match.number_of_games or 1)
        end_at = scheduled + timedelta(
            milliseconds=estimate_duration_ms(videogame_id, number_of_games)
        )

    opponent = None
    for entry in match.opponents:
        if entry.opponent.id != team_id:
            opponent = entry.opponent
            break

    entry_dict = {
        "start_time": scheduled,
        "end_time": end_at,
        "opponent": opponent.name,
        "tournament": get_full_game_name(match),
        "number_of_games": match.number_of_games,
    }

    if include_result:
        winner = match.winner
        if winner and winner.id == team_id:
            result = "won"
        elif winner and winner.id is not None:
            result = "lost"
        else:
            result = "draw"
        entry_dict["result"] = result
        entry_dict["score"] = extract_score(match)

    return entry_dict


def extract_score(match: Match) -> str | None:
    """TODO"""
    results = match.results or []
    if results:
        try:
            return (
                f"{results[0].score}-{results[1].score}" if len(results) > 1 else None
            )
        except (IndexError, TypeError):
            pass
    return None


async def build_team_tracker(
    hass: HomeAssistant, match: Match, team_id: int, language: str | None
) -> dict[str, Any]:
    """TODO"""
    opponent_1 = (
        match.opponents[0].opponent
        if match.opponents[0].type == "Team"
        else match.opponents[0]
    )
    opponent_2 = (
        match.opponents[1].opponent
        if match.opponents[1].type == "Team"
        else match.opponents[1]
    )
    if opponent_1.id == team_id:
        team = opponent_1
        opponent = opponent_2
    else:
        team = opponent_2
        opponent = opponent_1

    op_win_rate = (
        0 if "karmine" in opponent_1.slug or "karmine" in opponent_2.slug else 0.5
    )

    entry_dict = await build_match_attributes(hass, match, language)
    entry_dict.update(build_team_attributes(team, match.results, "team_", op_win_rate))
    entry_dict.update(
        build_team_attributes(opponent, match.results, "opponent_", op_win_rate)
    )

    return entry_dict


async def build_match_attributes(
    hass: HomeAssistant, match: Match, language: str | None
) -> dict[str, Any]:
    """TODO"""
    local_streams = [
        stream for stream in match.streams_list if stream.language == language
    ]
    local_stream = local_streams[0] if len(local_streams) > 0 else None

    state = "PRE"
    relative = await get_relative_date(
        hass, (match.begin_at or match.scheduled_at) or now(), language or "en"
    )
    if match.status == "running":
        state = "IN"
    if match.status in {"finished", "canceled"}:
        state = "POST"
        relative = await get_relative_date(
            hass, match.end_at or now(), language or "en"
        )

    return {
        "state": state,
        "sport": match.league.name if match.league else "Unknown",
        "league_name": get_full_game_name(match),
        "league_logo": match.league.image_url if match.league else None,
        "date": match.begin_at or match.scheduled_at,
        "last_update": now(),
        # Row 1
        "venue": match.videogame.name if match.videogame else None,
        # PRE
        "odds": translate(language, "down_distance_text")
        % str(get_bo(match.number_of_games or 0)),
        "down_distance_text": get_full_game_name(match),  # IN
        # Row 2
        "location": match.videogame_version.name
        if match.videogame_version
        else "No version",
        "overunder": get_full_game_name(match),  # PRE
        "tv_network": local_stream.raw_url if local_stream else None,  # IN
        "kickoff_in": relative,
        "clock": relative,
    }


def build_team_attributes(
    opponent: Opponent,
    results: list[Result],
    side: Literal["team_", "opponent_"],
    op_win_rate: int,
) -> dict[str, Any]:
    """TODO"""
    return {
        side + "name": opponent.name or "Unknown",
        side + "logo": opponent.image_url or "",
        side + "logo_dark": opponent.dark_mode_image_url or "",
        side + "score": results[0].score
        if results[0].team_id == opponent.id
        else results[1].score,
        side + "timeouts": results[0].score
        if results[0].team_id == opponent.id
        else results[1].score or 0,
        side + "win_probability": 1 if ("karmine" in opponent.slug) else op_win_rate,
        side + "colors": ["var(--primary-color)", "var(--accent-color)"],
        side + "homeaway": "home" if results[0].team_id == opponent.id else "away",
        side + "winner": results[0].team_id == opponent.id
        and results[0].score > results[1].score
        or results[1].team_id == opponent.id
        and results[1].score > results[0].score,
        side + "record": None,
        side + "rank": None,
    }


def get_full_game_name(match: Match) -> str:
    """TODO"""
    league_name = match.league.name if match.league else None
    serie_name = match.serie.full_name if match.serie else None
    tournament_name = match.tournament.name if match.tournament else None

    game_name = ""

    if league_name:
        game_name += "[" + league_name + "]"
    if serie_name:
        game_name += " " + serie_name
    if tournament_name:
        game_name += " " + tournament_name

    return game_name


def get_bo(number_of_games: int) -> int:
    """TODO"""
    return int((number_of_games - 1) / 2 + 1)


def get_opponent(match: Match, team_id: int) -> Any:
    """Get the opponent of a team in a match."""
    opponent_1 = (
        match.opponents[0].opponent
        if match.opponents[0].type == "Team"
        else match.opponents[0]
    )
    opponent_2 = (
        match.opponents[1].opponent
        if match.opponents[1].type == "Team"
        else match.opponents[1]
    )
    return opponent_2 if opponent_1.id == team_id else opponent_1


async def get_relative_date(hass: HomeAssistant, date: datetime, language: str) -> str:
    """TODO"""
    f_kwargs = {
        "delta": date - now(),
        "add_direction": True,
        "locale": LOCALE_MAP.get(language or "en"),
    }
    return await hass.async_add_executor_job(partial(format_timedelta, **f_kwargs))


def translate(language: str | None, string: str) -> str:
    """TODO"""
    translations = {
        "en": {
            "down_distance_text": "Best of %s",
        },
        "fr": {
            "down_distance_text": "Premier à %s",
        },
        None: {
            "down_distance_text": "Best of %s",
        },
    }
    return translations.get(language, translations.get(None)).get(string, string)
