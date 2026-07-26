"""DataUpdateCoordinator for Pandascore integration."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util.dt import utcnow

from . import utils
from .api import PandascoreAPI
from .const import CONF_TEAMS, CONF_TOKEN, DEFAULT_SCAN_INTERVAL
from .models import Match, Team

_LOGGER = logging.getLogger(__name__)


@dataclass
class TeamData:
    team: Team
    matches: list[Match]
    last_match: dict[str, Any]
    next_match: dict[str, Any]


class PandascoreDataUpdateCoordinator(DataUpdateCoordinator[dict[int, TeamData]]):
    """Coordinator to fetch teams and matches."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.token = str(entry.data.get(CONF_TOKEN) or "")
        self.selected_teams = entry.options.get(
            CONF_TEAMS, entry.data.get(CONF_TEAMS, [])
        )
        self.api = PandascoreAPI(hass, self.token)

        super().__init__(
            hass,
            _LOGGER,
            name="pandascore",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
            update_method=self._async_update_data,
        )

    async def _async_update_data(self) -> dict[int, TeamData]:
        """Fetch and return data for configured teams."""
        try:
            result: dict[int, TeamData] = {}
            if not self.selected_teams:
                return result

            # Year range
            dt_now = utcnow()
            start = datetime(dt_now.year, 1, 1, tzinfo=dt_now.tzinfo).date().isoformat()
            end = datetime(dt_now.year, 12, 31, tzinfo=dt_now.tzinfo).date().isoformat()

            for team in self.selected_teams:
                team_id = int(team.get("id"))
                matches = await self.api.async_get_matches(team_id, start, end)

                last_matches = [m for m in matches if m.status == "finished"]
                last_matches.sort(
                    key=lambda m: m.scheduled_at or m.begin_at or utcnow(), reverse=True
                )
                last_match = (
                    await self.build_match(last_matches[0], team_id)
                    if last_matches
                    else {}
                )

                next_matches = [
                    m
                    for m in matches
                    if m.status in {"not_started", "pending", "running"}
                ]
                next_matches.sort(
                    key=lambda m: m.scheduled_at or m.begin_at or utcnow()
                )
                next_match = (
                    await self.build_match(next_matches[0], team_id)
                    if next_matches
                    else {}
                )

                result[team_id] = TeamData(
                    team=team,
                    matches=matches,
                    last_match=last_match,
                    next_match=next_match,
                )

            return result
        except Exception as err:  # pylint: disable=broad-except
            raise UpdateFailed(err) from err

    async def build_match(self, match: Match, team_id: int):
        """TODO"""
        match_opponent = utils.get_opponent(match, team_id)

        match_mapped = await utils.build_team_tracker(
            self.hass, match, self.hass.config.language
        )
        match_mapped["team_record"] = await self.api.async_get_record(
            team_id, match.serie.id
        )
        match_mapped["opponent_record"] = await self.api.async_get_record(
            match_opponent.id, match.serie.id
        )

        return match_mapped
