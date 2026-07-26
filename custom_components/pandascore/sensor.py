"""Sensors for Pandascore teams."""

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import utcnow

from .const import CONF_TEAMS, DOMAIN
from .coordinator import PandascoreDataUpdateCoordinator, TeamData
from .utils import build_match_entry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    _: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    runtime = entry.runtime_data
    coordinator: PandascoreDataUpdateCoordinator = runtime["coordinator"]
    teams = entry.options.get(CONF_TEAMS, entry.data.get(CONF_TEAMS, []))
    entities = []
    for team in teams:
        entities.extend(_create_team_sensors(coordinator, team))
    async_add_entities(entities, True)


def _create_team_sensors(
    coordinator: PandascoreDataUpdateCoordinator, team: dict[str, Any]
) -> list[SensorEntity]:
    """Create all sensors for a single team (device)."""
    team_id = int(team.get("id") or -1)
    team_slug = team.get("slug", str(team_id))
    game_name = team.get("current_videogame", {}).get("name") or "Unknown"
    device_name = f"[{game_name}] {team.get('name')}"

    device_info = DeviceInfo(
        identifiers={(DOMAIN, f"pandascore_{team_slug}")},
        name=device_name,
        manufacturer="Pandascore",
        model=game_name,
        entry_type=DeviceEntryType.SERVICE,
    )

    return [
        PandascoreNameSensor(coordinator, team, team_id, team_slug, device_info),
        PandascoreGameSensor(coordinator, team, team_id, team_slug, device_info),
        PandascoreNextMatchSensor(coordinator, team, team_id, team_slug, device_info),
        PandascoreLastMatchSensor(coordinator, team, team_id, team_slug, device_info),
        PandascoreMatchesWonSensor(coordinator, team, team_id, team_slug, device_info),
        PandascoreMatchesLossSensor(coordinator, team, team_id, team_slug, device_info),
        PandascoreWinRateSensor(coordinator, team, team_id, team_slug, device_info),
        PandascoreMatchesPlayedSensor(
            coordinator, team, team_id, team_slug, device_info
        ),
        PandascoreUpcomingMatchesSensor(
            coordinator, team, team_id, team_slug, device_info
        ),
        TeamTrackerSensor(coordinator, team, team_id, team_slug, device_info),
    ]


class PandascoreTeamSensorBase(
    CoordinatorEntity[PandascoreDataUpdateCoordinator], SensorEntity
):
    """Base sensor for team data."""

    def __init__(
        self,
        # hass: HomeAssistant,
        coordinator: PandascoreDataUpdateCoordinator,
        team: dict[str, Any],
        team_id: int,
        team_slug: str,
        device_info: DeviceInfo,
        sensor_name: str,
    ) -> None:
        super().__init__(coordinator, _LOGGER)
        self._team = team
        self._team_id = team_id
        self._attr_unique_id = f"{team_slug}.{sensor_name}"
        self._attr_has_entity_name = True
        self._attr_translation_key = f"{sensor_name}"
        self._attr_device_info = device_info

    def _get_team_data(self) -> TeamData | None:
        return (self.coordinator.data or {}).get(self._team_id)


class PandascoreNameSensor(PandascoreTeamSensorBase):
    """Name sensor."""

    _attr_icon = "mdi:account-group"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, sensor_name="name", **kwargs)

    @property
    def native_value(self) -> str:
        return self._team.get("name", "Unknown")


class PandascoreGameSensor(PandascoreTeamSensorBase):
    """Game sensor."""

    _attr_icon = "mdi:controller"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, sensor_name="game", **kwargs)

    @property
    def native_value(self) -> str:
        return (
            str((self._team.get("current_videogame") or {}).get("name")).lower()
            or "Unknown"
        )


class PandascoreNextMatchSensor(PandascoreTeamSensorBase):
    """Next match sensor."""

    _attr_icon = "mdi:play-network-outline"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, sensor_name="next_match", **kwargs)

    @property
    def native_value(self) -> str | None:
        data = self._get_team_data()
        if not data:
            return None
        return data.next_match.get("state") or "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self._get_team_data()
        if not data:
            return {}
        return data.next_match or {}


class PandascoreLastMatchSensor(PandascoreTeamSensorBase):
    """Last match sensor."""

    _attr_icon = "mdi:console-network-outline"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, sensor_name="last_match", **kwargs)

    @property
    def native_value(self) -> str | None:
        data = self._get_team_data()
        if not data:
            return None
        return data.last_match.get("state") or "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self._get_team_data()
        if not data:
            return {}
        return data.last_match or {}


class PandascoreMatchesWonSensor(PandascoreTeamSensorBase):
    """Matches won sensor."""

    _attr_icon = "mdi:check-network-outline"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, sensor_name="matches_won", **kwargs)

    @property
    def native_value(self) -> int:
        data = self._get_team_data()
        if not data:
            return 0
        won = sum(1 for m in data.matches if m.winner_id == self._team_id)
        return won


class PandascoreMatchesLossSensor(PandascoreTeamSensorBase):
    """Matches loss sensor."""

    _attr_icon = "mdi:close-network-outline"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, sensor_name="matches_loss", **kwargs)

    @property
    def native_value(self) -> int:
        data = self._get_team_data()
        if not data:
            return 0
        loss = sum(
            1
            for m in data.matches
            if m.winner_id != self._team_id and m.status == "finished"
        )
        return loss


class PandascoreWinRateSensor(PandascoreTeamSensorBase):
    """Win rate sensor."""

    _attr_icon = "mdi:trophy"
    _attr_native_unit_of_measurement = "%"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, sensor_name="win_rate", **kwargs)

    @property
    def native_value(self) -> float | None:
        data = self._get_team_data()
        if not data:
            return None
        won = sum(1 for m in data.matches if m.winner_id == self._team_id)
        loss = sum(
            1
            for m in data.matches
            if m.winner_id != self._team_id and m.status == "finished"
        )
        played = won + loss
        win_rate = round(won / played, 4) * 100 if played > 0 else None
        return win_rate


class PandascoreMatchesPlayedSensor(PandascoreTeamSensorBase):
    """Matches played sensor."""

    _attr_icon = "mdi:network-outline"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, sensor_name="matches_played", **kwargs)

    @property
    def native_value(self) -> int:
        data = self._get_team_data()
        if not data:
            return 0
        return len([m for m in data.matches if m.status == "finished"])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self._get_team_data()
        if not data:
            return {"matches": []}
        past = [m for m in data.matches if m.status == "finished"]
        past.sort(key=lambda m: m.scheduled_at or m.begin_at or utcnow(), reverse=True)
        return {
            "matches": [
                build_match_entry(self._team_id, m, include_result=True) for m in past
            ]
        }


class PandascoreUpcomingMatchesSensor(PandascoreTeamSensorBase):
    """Upcoming matches sensor."""

    _attr_icon = "mdi:help-network-outline"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, sensor_name="upcoming_matches", **kwargs)

    @property
    def native_value(self) -> int:
        data = self._get_team_data()
        if not data:
            return 0
        return len([m for m in data.matches if m.status in {"not_started", "pending"}])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self._get_team_data()
        if not data:
            return {"matches": []}
        upcoming = [m for m in data.matches if m.status in {"not_started", "pending"}]
        upcoming.sort(key=lambda m: m.scheduled_at or m.begin_at or utcnow())
        return {"matches": [build_match_entry(self._team_id, m) for m in upcoming]}


class TeamTrackerSensor(PandascoreTeamSensorBase):
    """Upcoming matches sensor."""

    _attr_icon = "mdi:test-tube"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, sensor_name="teamTracker", **kwargs)

    @property
    def native_value(self) -> str:
        data = self._get_team_data()
        if not data:
            return "Unavailable"
        if data.next_match:
            return data.next_match.get("state") or "Unknown"
        if data.last_match:
            return data.last_match.get("state") or "Unknown"
        return "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self._get_team_data()
        if not data:
            return {}
        if data.next_match:
            return data.next_match
        return data.last_match or {}
