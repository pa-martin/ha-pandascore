"""DataUpdateCoordinator for Pandascore integration."""

import asyncio
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
    """
    Store all data associated with a configured PandaScore team.


    :ivar team: The PandaScore team information.
    :ivar matches: The list of matches retrieved for the team.
    :ivar last_match: The mapped data of the team's most recently finished
        match, or an empty dictionary if no finished match is available.
    :ivar next_match: The mapped data of the team's next upcoming or currently
        active match, or an empty dictionary if no such match is available.
    """

    team: Team
    matches: list[Match]
    last_match: dict[str, Any]
    next_match: dict[str, Any]


class PandascoreDataUpdateCoordinator(DataUpdateCoordinator[dict[int, TeamData]]):
    """
    Coordinate data updates for the PandaScore integration.


    The coordinator periodically retrieves match data for all teams selected
    in the PandaScore configuration entry. It identifies the most recent
    finished match and the next upcoming or currently active match for each
    team, then exposes the resulting data to Home Assistant platforms.

    :param hass: The Home Assistant instance.
    :param entry: The PandaScore configuration entry containing the API token
        and the list of selected teams.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """
        Initialize the PandaScore data update coordinator.

        The coordinator creates a PandaScore API client and configures the
        update interval using the default PandaScore scan interval.

        :param hass: The Home Assistant instance.
        :param entry: The PandaScore configuration entry containing the API
            token and selected teams.
        """
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
        """
        Fetch and process data for all configured teams.

        Matches are retrieved for the current calendar year. For each
        configured team, the most recent finished match and the next upcoming
        or currently active match are identified and mapped to tracker data.

        :return: A dictionary mapping each PandaScore team identifier to its
            corresponding :class:`TeamData` instance. An empty dictionary is
            returned when no teams are configured.
        :raises UpdateFailed: If an unexpected error occurs while fetching
            or processing the team and match data.
        """
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
                    await self._async_build_match(last_matches[0], team_id)
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
                    await self._async_build_match(next_matches[0], team_id)
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

    async def _async_build_match(self, match: Match, team_id: int) -> dict[str, Any]:
        """
        Build a mapped representation of a match for a specific team.

        The match is converted into the attribute structure used by the
        integration's match tracker. The team's and opponent's series
        records are then retrieved and added to the mapped match data.

        :param match: The PandaScore match to map.
        :param team_id: The identifier of the team for which the match
            is being mapped.
        :return: A dictionary containing the mapped match tracker attributes,
            including the selected team's record and the opponent's record
            for the match series.
        """
        match_opponent = utils.get_opponent(match, team_id)

        match_mapped = await utils.async_build_team_tracker(
            self.hass, match, team_id, self.hass.config.language
        )
        team_record, opponent_record = await asyncio.gather(
            self.api.async_get_record(team_id, str(match.serie.id or "")),
            self.api.async_get_record(
                match_opponent.id or -1, str(match.serie.id or "")
            ),
        )

        match_mapped["team_record"] = team_record
        match_mapped["opponent_record"] = opponent_record

        return match_mapped
