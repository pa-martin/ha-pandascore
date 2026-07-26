from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from marshmallow_dataclass import class_schema


@dataclass
class League:
    id: Optional[int]
    image_url: Optional[str]
    modified_at: Optional[str]
    name: Optional[str]
    slug: Optional[str]
    url: Optional[str]


@dataclass
class Live:
    opens_at: Optional[str]
    supported: Optional[bool]
    url: Optional[str]


@dataclass
class Serie:
    begin_at: Optional[datetime]
    end_at: Optional[datetime]
    full_name: Optional[str]
    id: Optional[int]
    league_id: Optional[int]
    modified_at: Optional[datetime]
    name: Optional[str]
    season: Optional[str]
    slug: Optional[str]
    winner_id: Optional[int]
    winner_type: Optional[str]
    year: Optional[int]


@dataclass
class Stream:
    embed_url: Optional[str]
    language: Optional[str]
    main: Optional[bool]
    official: Optional[bool]
    raw_url: Optional[str]


@dataclass
class Tournament:
    begin_at: Optional[datetime]
    country: Optional[str]
    detailed_stats: Optional[bool]
    end_at: Optional[datetime]
    has_bracket: Optional[bool]
    id: Optional[int]
    league_id: Optional[int]
    live_supported: Optional[bool]
    modified_at: Optional[datetime]
    name: Optional[str]
    prizepool: Optional[str]
    region: Optional[str]
    serie_id: Optional[int]
    slug: Optional[str]
    tier: Optional[str]
    type: Optional[str]
    winner_id: Optional[int]
    winner_type: Optional[str]


@dataclass
class Videogame:
    id: Optional[int]
    name: Optional[str]
    slug: Optional[str]


@dataclass
class VideogameTitle:
    id: Optional[int]
    name: Optional[str]
    slug: Optional[str]
    videogame_id: Optional[int]


@dataclass
class VideogameVersion:
    name: Optional[str]
    current: Optional[bool]


@dataclass
class Player:
    id: Optional[int]
    name: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    slug: Optional[str]


@dataclass
class Team:
    acronym: Optional[str]
    current_videogame: Optional[Videogame]
    dark_mode_image_url: Optional[str]
    id: Optional[int]
    image_url: Optional[str]
    location: Optional[str]
    modified_at: Optional[datetime]
    name: Optional[str]
    players: Optional[list[Player]]
    slug: Optional[str]


@dataclass
class Opponent(Team):
    type: Optional[str]
    opponent: Optional[Team]


@dataclass
class Game:
    begin_at: Optional[datetime]
    complete: Optional[bool]
    detailed_stats: Optional[bool]
    end_at: Optional[datetime]
    finished: Optional[bool]
    forfeit: Optional[bool]
    id: Optional[int]
    length: Optional[int]
    match_id: Optional[int]
    position: Optional[int]
    status: Optional[str]
    winner: Optional[Opponent]
    winner_type: Optional[str]


@dataclass
class Result:
    score: Optional[int]
    team_id: Optional[int]


@dataclass
class Match:
    begin_at: Optional[datetime]
    detailed_stats: Optional[bool]
    draw: Optional[bool]
    end_at: Optional[datetime]
    forfeit: Optional[bool]
    game_advantage: Optional[str]

    games: Optional[list[Game]]

    id: Optional[int]

    league: Optional[League]
    league_id: Optional[int]

    live: Optional[Live]

    match_type: Optional[str]
    modified_at: Optional[datetime]
    name: Optional[str]
    number_of_games: Optional[int]

    opponents: Optional[list[Opponent]]

    original_scheduled_at: Optional[datetime]
    rescheduled: Optional[bool]

    results: Optional[list[Result]]

    scheduled_at: Optional[datetime]

    serie: Optional[Serie]
    serie_id: Optional[int]

    slug: Optional[str]
    status: Optional[str]

    streams_list: list[Stream]

    tournament: Optional[Tournament]
    tournament_id: Optional[int]

    videogame: Optional[Videogame]
    videogame_title: Optional[VideogameTitle]
    videogame_version: Optional[VideogameVersion]

    winner: Optional[Opponent]
    winner_id: Optional[int]
    winner_type: Optional[str]


MatchSchema = class_schema(Match)
