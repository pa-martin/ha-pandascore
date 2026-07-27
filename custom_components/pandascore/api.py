"""Async client for the Pandascore API."""

import logging
from typing import Any

from aiohttp import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import BASE_URL, HEADER_ACCEPT
from .models import Match, MatchSchema

_LOGGER = logging.getLogger(__name__)


class PandascoreAPI:
    """Minimal asynchronous client for the PandaScore API."""

    def __init__(self, hass: HomeAssistant, token: str) -> None:
        """
        Initialize the PandaScore API client.

        :param hass: The Home Assistant instance used to retrieve the shared
            HTTP client session.
        :param token: The PandaScore API authentication token.
        """
        self.hass = hass
        self.token = token
        self._session = async_get_clientsession(hass)

    async def async_search_teams(self, name: str) -> list[dict[str, Any]]:
        """
        Search for teams by name using the PandaScore API.

        :param name: The name or search term used to find matching teams.
        :return: A list of dictionaries containing the matching team data.
            An empty list is returned if the request fails or the API returns
            a non-successful HTTP status.
        """
        url = f"{BASE_URL}/teams"
        params = {"search[name]": name}
        headers = {"accept": HEADER_ACCEPT, "authorization": f"Bearer {self.token}"}
        try:
            async with self._session.get(url, params=params, headers=headers) as resp:
                if resp.status != 200:
                    _LOGGER.warning("Teams search failed: %s", resp.status)
                    return []
                return await resp.json()
        except ClientError:
            _LOGGER.exception("Teams search connection error")
            return []

    async def async_get_matches(
        self, team_id: int, start: str, end: str
    ) -> list[Match]:
        """
        Retrieve matches for a team within a specified date range.

        The date range is sent to the PandaScore API as an ISO date string
        range using the ``scheduled_at`` field. The API response is then
        deserialized into a list of :class:`Match` objects.

        :param team_id: The PandaScore identifier of the team whose matches
            should be retrieved.
        :param start: The start of the date range as an ISO-formatted date
            or datetime string.
        :param end: The end of the date range as an ISO-formatted date
            or datetime string.
        :return: A list of parsed :class:`Match` objects. An empty list is
            returned if the API request fails, returns a non-successful HTTP
            status, or the response cannot be mapped to the expected model.
        """
        url = f"{BASE_URL}/teams/{team_id}/matches"
        params = {"range[scheduled_at]": f"{start},{end}"}
        headers = {"accept": HEADER_ACCEPT, "authorization": f"Bearer {self.token}"}
        try:
            async with self._session.get(url, params=params, headers=headers) as resp:
                if resp.status != 200:
                    _LOGGER.warning(
                        "Matches fetch failed for id %s: %s", team_id, resp.status
                    )
                    return []
                data = await resp.json()
                schema = MatchSchema(many=True)
                matches = schema.load(data)
                return matches
        except ClientError as err:
            _LOGGER.warning(
                "Matches fetch connection error for id %s: %s", team_id, err
            )
            return []
        except Exception:
            _LOGGER.exception("Matches mapping error for id %s", team_id)
            return []

    async def async_get_record(self, team_id: int, serie_id: str) -> str | None:
        """
        Retrieve the win-loss record of a team within a specific series.

        Only finished matches belonging to the specified series are retrieved.
        The record is calculated from the returned matches by counting the
        number of matches won by the specified team and treating the remaining
        matches as losses.

        :param team_id: The PandaScore identifier of the team whose record
            should be retrieved.
        :param serie_id: The PandaScore identifier of the series for which
            the team's record should be calculated.
        :return: The team's win-loss record formatted as ``"wins-losses"``,
            for example ``"3-1"``. ``None`` is returned if the API request
            fails, returns a non-successful HTTP status, or the response
            cannot be mapped to the expected model.
        """
        url = f"{BASE_URL}/teams/{team_id}/matches"
        params = {"filter[finished]": "true", "filter[serie_id]": str(serie_id)}
        headers = {"accept": HEADER_ACCEPT, "authorization": f"Bearer {self.token}"}
        try:
            async with self._session.get(url, params=params, headers=headers) as resp:
                if resp.status != 200:
                    _LOGGER.warning(
                        "Matches fetch failed for id %s: %s", team_id, resp.status
                    )
                    return None
                data = await resp.json()
                schema = MatchSchema(many=True)
                matches = schema.load(data)
                wins = sum(1 for match in matches if match.winner_id == team_id)
                losses = len(matches) - wins
                return f"{wins}-{losses}"
        except ClientError as err:
            _LOGGER.warning(
                "Matches fetch connection error for id %s: %s", team_id, err
            )
            return None
        except Exception:
            _LOGGER.exception("Matches mapping error for id %s", team_id)
            return None
