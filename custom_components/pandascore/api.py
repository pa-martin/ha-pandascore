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
    """Minimal async client for Pandascore."""

    def __init__(self, hass: HomeAssistant, token: str) -> None:
        self.hass = hass
        self.token = token
        self._session = async_get_clientsession(hass)

    async def async_search_teams(self, name: str) -> list[dict[str, Any]]:
        """Search teams by name."""
        url = f"{BASE_URL}/teams"
        params = {"search[name]": name}
        headers = {"accept": HEADER_ACCEPT,
                   "authorization": f"Bearer {self.token}"}
        try:
            async with self._session.get(url, params=params, headers=headers) as resp:
                if resp.status != 200:
                    _LOGGER.warning("Teams search failed: %s", resp.status)
                    return []
                return await resp.json()
        except ClientError as err:
            _LOGGER.exception("Teams search connection error: %s", err)
            return []

    async def async_get_matches(self, team_id: int, start: str, end: str) -> list[Match]:
        """Get matches for a team between start and end (ISO date strings)."""
        url = f"{BASE_URL}/teams/{team_id}/matches"
        params = {"range[scheduled_at]": f"{start},{end}"}
        headers = {"accept": HEADER_ACCEPT,
                   "authorization": f"Bearer {self.token}"}
        try:
            async with self._session.get(url, params=params, headers=headers) as resp:
                if resp.status != 200:
                    _LOGGER.warning(
                        "Matches fetch failed for id %s: %s", team_id, resp.status)
                    return []
                data = await resp.json()
                schema = MatchSchema(many=True)
                x = schema.load(data)
                return x
        except ClientError as err:
            _LOGGER.warning(
                "Matches fetch connection error for id %s: %s", team_id, err)
            return []
        except Exception as err:
            _LOGGER.exception(
                "Matches mapping error for id %s: %s", team_id, err)
            return []

    async def async_get_record(self, team_id: int, serie_id: str) -> str | None:
        """TODO"""
        url = f"{BASE_URL}/teams/{team_id}/matches"
        params = {"filter[finished]": "true",
                  "filter[serie_id]": str(serie_id)}
        headers = {"accept": HEADER_ACCEPT,
                   "authorization": f"Bearer {self.token}"}
        try:
            async with self._session.get(url, params=params, headers=headers) as resp:
                if resp.status != 200:
                    _LOGGER.warning(
                        "Matches fetch failed for id %s: %s", team_id, resp.status)
                    return None
                data = await resp.json()
                schema = MatchSchema(many=True)
                x = schema.load(data)
                wins = sum(1 for match in x if match.winner_id == team_id)
                losses = len(x) - wins
                return f"{wins}-{losses}"
        except ClientError as err:
            _LOGGER.warning(
                "Matches fetch connection error for id %s: %s", team_id, err)
            return None
        except Exception as err:
            _LOGGER.exception(
                "Matches mapping error for id %s: %s", team_id, err)
            return None
