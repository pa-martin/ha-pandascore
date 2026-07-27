"""Data models for the PandaScore API.

This module defines the dataclasses used to deserialize PandaScore API
responses into strongly typed Python objects using marshmallow-dataclass.
"""

from dataclasses import dataclass
from datetime import datetime

from marshmallow_dataclass import class_schema


@dataclass
class League:
    """Represent a PandaScore league."""

    id: int | None
    """Unique identifier of the league."""
    image_url: str | None
    """URL of the league logo or image."""
    modified_at: str | None
    """Timestamp of the last modification of the league."""
    name: str | None
    """Display name of the league."""
    slug: str | None
    """URL-friendly identifier of the league."""
    url: str | None
    """URL of the league on PandaScore."""


@dataclass
class Live:
    """Represent the live streaming information of a match."""

    opens_at: str | None
    """Timestamp indicating when the live stream becomes available."""
    supported: bool | None
    """Whether live streaming is supported for the match."""
    url: str | None
    """URL of the live stream."""


@dataclass
class Serie:
    """Represent a PandaScore esports series."""

    begin_at: datetime | None
    """Start date and time of the series."""
    end_at: datetime | None
    """End date and time of the series."""
    full_name: str | None
    """Full display name of the series."""
    id: int | None
    """Unique identifier of the series."""
    league_id: int | None
    """Identifier of the league containing the series."""
    modified_at: datetime | None
    """Timestamp of the last modification of the series."""
    name: str | None
    """Display name of the series."""
    season: str | None
    """Season associated with the series."""
    slug: str | None
    """URL-friendly identifier of the series."""
    winner_id: int | None
    """Identifier of the team that won the series."""
    winner_type: str | None
    """Type of the series winner."""
    year: int | None
    """Year in which the series takes place."""


@dataclass
class Stream:
    """Represent a broadcast stream associated with a match."""

    embed_url: str | None
    """URL used to embed the stream."""
    language: str | None
    """Language of the stream."""
    main: bool | None
    """Whether the stream is the main stream."""
    official: bool | None
    """Whether the stream is an official broadcast."""
    raw_url: str | None
    """Direct URL of the stream."""


@dataclass
class Tournament:
    """Represent a PandaScore tournament."""

    begin_at: datetime | None
    """Start date and time of the tournament."""
    country: str | None
    """Country where the tournament takes place."""
    detailed_stats: bool | None
    """Whether detailed statistics are available."""
    end_at: datetime | None
    """End date and time of the tournament."""
    has_bracket: bool | None
    """Whether the tournament has a bracket."""
    id: int | None
    """Unique identifier of the tournament."""
    league_id: int | None
    """Identifier of the league containing the tournament."""
    live_supported: bool | None
    """Whether live coverage is supported for the tournament."""
    modified_at: datetime | None
    """Timestamp of the last modification of the tournament."""
    name: str | None
    """Display name of the tournament."""
    prizepool: str | None
    """Prize pool of the tournament."""
    region: str | None
    """Region associated with the tournament."""
    serie_id: int | None
    """Identifier of the series containing the tournament."""
    slug: str | None
    """URL-friendly identifier of the tournament."""
    tier: str | None
    """Competitive tier of the tournament."""
    type: str | None
    """Type of the tournament."""
    winner_id: int | None
    """Identifier of the tournament winner."""
    winner_type: str | None
    """Type of the tournament winner."""


@dataclass
class Videogame:
    """Represent a videogame supported by PandaScore."""

    id: int | None
    """Unique identifier of the videogame."""
    name: str | None
    """Display name of the videogame."""
    slug: str | None
    """URL-friendly identifier of the videogame."""


@dataclass
class VideogameTitle:
    """Represent a specific title or version of a videogame."""

    id: int | None
    """Unique identifier of the videogame title."""
    name: str | None
    """Display name of the videogame title."""
    slug: str | None
    """URL-friendly identifier of the videogame title."""
    videogame_id: int | None
    """Identifier of the parent videogame."""


@dataclass
class VideogameVersion:
    """Represent a specific version of a videogame."""

    name: str | None
    """Display name of the videogame version."""
    current: bool | None
    """Whether this is the current version of the videogame."""


@dataclass
class Player:
    """Represent an esports player."""

    id: int | None
    """Unique identifier of the player."""
    name: str | None
    """Display name of the player."""
    first_name: str | None
    """First name of the player."""
    last_name: str | None
    """Last name of the player."""
    slug: str | None
    """URL-friendly identifier of the player."""


@dataclass
class Team:
    """Represent an esports team."""

    acronym: str | None
    """Short acronym used to identify the team."""
    current_videogame: Videogame | None
    """Videogame currently associated with the team."""
    dark_mode_image_url: str | None
    """URL of the team logo optimized for dark mode."""
    id: int | None
    """Unique identifier of the team."""
    image_url: str | None
    """URL of the team's logo or image."""
    location: str | None
    """Location or country associated with the team."""
    modified_at: datetime | None
    """Timestamp of the last modification of the team."""
    name: str | None
    """Display name of the team."""
    players: list[Player] | None
    """Players currently associated with the team."""
    slug: str | None
    """URL-friendly identifier of the team."""


@dataclass
class Opponent(Team):
    """Represent an opponent entry associated with a match.

    PandaScore opponent objects can contain either a team directly or
    an opponent wrapper describing the type of participant.
    """

    type: str | None
    """Type of the opponent, such as ``"Team"``."""
    opponent: Team | None
    """Team information contained in the opponent entry."""


@dataclass
class Game:
    """Represent an individual game played within a match."""

    begin_at: datetime | None
    """Start date and time of the game."""
    complete: bool | None
    """Whether the game has been completed."""
    detailed_stats: bool | None
    """Whether detailed statistics are available for the game."""
    end_at: datetime | None
    """End date and time of the game."""
    finished: bool | None
    """Whether the game has finished."""
    forfeit: bool | None
    """Whether the game ended due to a forfeit."""
    id: int | None
    """Unique identifier of the game."""
    length: int | None
    """Duration of the game, in seconds."""
    match_id: int | None
    """Identifier of the match containing the game."""
    position: int | None
    """Position of the game within the match series."""
    status: str | None
    """Current status of the game."""
    winner: Opponent | None
    """Opponent that won the game."""
    winner_type: str | None
    """Type of the game winner."""


@dataclass
class Result:
    """Represent the score of a team in a match."""

    score: int | None
    """Score achieved by the team."""
    team_id: int | None
    """Identifier of the team associated with the score."""


@dataclass
class Match:
    """Represent an esports match retrieved from the PandaScore API."""

    begin_at: datetime | None
    """Actual start date and time of the match."""
    detailed_stats: bool | None
    """Whether detailed statistics are available for the match."""
    draw: bool | None
    """Whether the match ended in a draw."""
    end_at: datetime | None
    """End date and time of the match."""
    forfeit: bool | None
    """Whether the match ended due to a forfeit."""
    game_advantage: str | None
    """Game advantage applied to one of the participants, if any."""

    games: list[Game] | None
    """List of individual games played as part of the match."""

    id: int | None
    """Unique identifier of the match."""

    league: League | None
    """League associated with the match."""
    league_id: int | None
    """Identifier of the league associated with the match."""

    live: Live | None
    """Live streaming information for the match."""

    match_type: str | None
    """Type of the match."""
    modified_at: datetime | None
    """Timestamp of the last modification of the match."""
    name: str | None
    """Display name of the match."""
    number_of_games: int | None
    """Maximum number of games that can be played in the match."""

    opponents: list[Opponent] | None
    """Participants competing in the match."""

    original_scheduled_at: datetime | None
    """Original scheduled date and time before any rescheduling."""
    rescheduled: bool | None
    """Whether the match has been rescheduled."""

    results: list[Result] | None
    """Scores of the teams participating in the match."""

    scheduled_at: datetime | None
    """Scheduled date and time of the match."""

    serie: Serie | None
    """Series associated with the match."""
    serie_id: int | None
    """Identifier of the series associated with the match."""

    slug: str | None
    """URL-friendly identifier of the match."""
    status: str | None
    """Current status of the match."""

    streams_list: list[Stream]
    """List of broadcast streams available for the match."""

    tournament: Tournament | None
    """Tournament associated with the match."""
    tournament_id: int | None
    """Identifier of the tournament associated with the match."""

    videogame: Videogame | None
    """Videogame played during the match."""
    videogame_title: VideogameTitle | None
    """Specific title of the videogame played during the match."""
    videogame_version: VideogameVersion | None
    """Videogame version used for the match."""

    winner: Opponent | None
    """Opponent that won the match."""
    winner_id: int | None
    """Identifier of the opponent that won the match."""
    winner_type: str | None
    """Type of the match winner."""


MatchSchema = class_schema(Match)
"""Marshmallow schema used to deserialize PandaScore API match responses."""
