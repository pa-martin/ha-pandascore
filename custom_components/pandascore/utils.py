"""Utility helpers for Pandascore match formatting and translations."""

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
    """
    Estimate the duration of a match in milliseconds based on the videogame and number of games.
    :param videogame_id: the id of the game
    :param number_of_games: the maximal numbers of games (eg: 5 in case of bo5)
    :return: a duration in milliseconds
    """
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
    """
    Build a dictionary representing a match entry for a team.

    If the match does not have an explicit end time but has a scheduled or
    start time, the end time is estimated from the videogame and the maximum
    number of games.

    :param team_id: The identifier of the team for which the match entry
        is being built.
    :param match: The match to format.
    :param include_result: Whether to include the match result and score
        in the returned dictionary.
    :return: A dictionary containing the match start and end times,
        the opponent, tournament name, and maximum number of games.
        If ``include_result`` is ``True``, the dictionary also contains
        the match result and score.
    """
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
    """
    Extract the final series score from a match.


    The score is formatted as ``"home-away"`` using the scores of the first
    two match results. If fewer than two results are available or the score
    cannot be derived, ``None`` is returned.

    :param match: The match from which to extract the series score.
    :return: The formatted series score as ``"home-away"``, or ``None``
        if the score cannot be determined.
    """
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
    """
    Build the complete attribute payload for a team's match tracker card.


    The returned dictionary combines common match attributes with
    team-specific and opponent-specific attributes.

    :param hass: The Home Assistant instance used for asynchronous operations
        such as localized date formatting.
    :param match: The match for which the tracker attributes are generated.
    :param team_id: The identifier of the team whose tracker attributes
        are being generated.
    :param language: The language code used for localized strings and stream
        selection. If ``None``, the default language is used.
    :return: A dictionary containing common match attributes, team attributes,
        and opponent attributes for the match tracker card.
    """
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
    """
    Build the common match attributes shared by both sides of a tracker.


    The function determines the current match state, selects the stream
    corresponding to the requested language, and builds localized relative
    date information.

    :param hass: The Home Assistant instance used for asynchronous date
        formatting.
    :param match: The match for which attributes are generated.
    :param language: The language code used to select the local stream
        and translate UI strings. If ``None``, the default language is used.
    :return: A dictionary containing common match attributes, including
        the match state, sport, league, league logo, date, last update,
        venue, odds, location, TV network, and relative kickoff time.
    """
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
        "sport": match.league.name if match.league else None,
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
    op_win_rate: float,
) -> dict[str, Any]:
    """
    Build side-specific attributes for a team or its opponent.


    The returned attributes use the provided prefix to distinguish between
    the tracked team and its opponent.

    :param opponent: The team or opponent for which attributes are generated.
    :param results: The list of match results used to determine the score,
        home/away status, and winner.
    :param side: The attribute prefix to use. Must be either ``"team_"``
        or ``"opponent_"``.
    :param op_win_rate: The default win probability assigned to the opponent
        unless the team is identified as Karmine Corp.
    :return: A dictionary containing side-specific attributes such as
        name, logos, score, timeouts, win probability, colors, home/away
        status, winner status, record, and rank.
    """
    return {
        side + "name": opponent.name or None,
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
    """
    Return the full display name of a match.


    The display name is constructed from the league name, series full name,
    and tournament name when these values are available.

    :param match: The match from which to build the display name.
    :return: A formatted string containing the available league, series,
        and tournament names.
    """
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
    """
    Return the best-of length for a match series.


    :param number_of_games: The maximum number of games that can be played
        in the series.
    :return: The best-of length corresponding to the provided number of games,
        for example ``3`` for a best-of-three (BO3) series.
    """
    return int((number_of_games - 1) / 2 + 1)


def get_opponent(match: Match, team_id: int) -> Opponent:
    """
    Get the opponent of a team in a match.


    :param match: The match containing the team and its opponent.
    :param team_id: The identifier of the team for which the opponent
        should be returned.
    :return: The opponent of the specified team.
    """
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
    """
    Format a date as a localized relative time string.


    The relative duration between the provided date and the current time
    is calculated and formatted using Babel. The formatting operation
    is executed in the Home Assistant executor to avoid blocking
    the event loop.

    :param hass: The Home Assistant instance used to execute the formatting
        operation outside the event loop.
    :param date: The date and time to format.
    :param language: The language code used to select the locale.
        Supported language codes are ``fr``, ``en``, ``de``, and ``es``.
    :return: A localized relative time string, such as ``"in 2 days"``
        or ``"il y a 5 minutes"``.
    """
    f_kwargs = {
        "delta": date - now(),
        "add_direction": True,
        "locale": LOCALE_MAP.get(language or "en"),
    }
    return await hass.async_add_executor_job(partial(format_timedelta, **f_kwargs))


def translate(language: str | None, string: str) -> str:
    """
    Translate a UI string into the requested language.


    If the requested language or translation key is not available, the
    original string is returned as a fallback.

    :param language: The language code used to select the translation.
        Supported language codes are ``fr``, ``en``, ``de``, and ``es``.
        If ``None``, English is used as the default language.
    :param string: The translation key to translate.
    :return: The translated string, or the original string if no translation
        is available.
    """
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
