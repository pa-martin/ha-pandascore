from dataclasses import dataclass
from datetime import datetime

from marshmallow_dataclass import class_schema


@dataclass
class League:
    id: int | None
    image_url: str | None
    modified_at: str | None
    name: str | None
    slug: str | None
    url: str | None


@dataclass
class Live:
    opens_at: str | None
    supported: bool | None
    url: str | None


@dataclass
class Serie:
    begin_at: datetime | None
    end_at: datetime | None
    full_name: str | None
    id: int | None
    league_id: int | None
    modified_at: datetime | None
    name: str | None
    season: str | None
    slug: str | None
    winner_id: int | None
    winner_type: str | None
    year: int | None


@dataclass
class Stream:
    embed_url: str | None
    language: str | None
    main: bool | None
    official: bool | None
    raw_url: str | None


@dataclass
class Tournament:
    begin_at: datetime | None
    country: str | None
    detailed_stats: bool | None
    end_at: datetime | None
    has_bracket: bool | None
    id: int | None
    league_id: int | None
    live_supported: bool | None
    modified_at: datetime | None
    name: str | None
    prizepool: str | None
    region: str | None
    serie_id: int | None
    slug: str | None
    tier: str | None
    type: str | None
    winner_id: int | None
    winner_type: str | None


@dataclass
class Videogame:
    id: int | None
    name: str | None
    slug: str | None


@dataclass
class VideogameTitle:
    id: int | None
    name: str | None
    slug: str | None
    videogame_id: int | None


@dataclass
class VideogameVersion:
    name: str | None
    current: bool | None


@dataclass
class Player:
    id: int | None
    name: str | None
    first_name: str | None
    last_name: str | None
    slug: str | None


@dataclass
class Team:
    acronym: str | None
    current_videogame: Videogame | None
    dark_mode_image_url: str | None
    id: int | None
    image_url: str | None
    location: str | None
    modified_at: datetime | None
    name: str | None
    players: list[Player] | None
    slug: str | None


@dataclass
class Opponent(Team):
    type: str | None
    opponent: Team | None


@dataclass
class Game:
    begin_at: datetime | None
    complete: bool | None
    detailed_stats: bool | None
    end_at: datetime | None
    finished: bool | None
    forfeit: bool | None
    id: int | None
    length: int | None
    match_id: int | None
    position: int | None
    status: str | None
    winner: Opponent | None
    winner_type: str | None


@dataclass
class Result:
    score: int | None
    team_id: int | None


@dataclass
class Match:
    begin_at: datetime | None
    detailed_stats: bool | None
    draw: bool | None
    end_at: datetime | None
    forfeit: bool | None
    game_advantage: str | None

    games: list[Game] | None

    id: int | None

    league: League | None
    league_id: int | None

    live: Live | None

    match_type: str | None
    modified_at: datetime | None
    name: str | None
    number_of_games: int | None

    opponents: list[Opponent] | None

    original_scheduled_at: datetime | None
    rescheduled: bool | None

    results: list[Result] | None

    scheduled_at: datetime | None

    serie: Serie | None
    serie_id: int | None

    slug: str | None
    status: str | None

    streams_list: list[Stream]

    tournament: Tournament | None
    tournament_id: int | None

    videogame: Videogame | None
    videogame_title: VideogameTitle | None
    videogame_version: VideogameVersion | None

    winner: Opponent | None
    winner_id: int | None
    winner_type: str | None


MatchSchema = class_schema(Match)
