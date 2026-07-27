"""Sensors for Pandascore teams."""

import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import utcnow

from .const import CONF_TEAMS, DOMAIN
from .coordinator import PandascoreDataUpdateCoordinator, TeamData
from .utils import build_match_entry

_LOGGER = logging.getLogger(__name__)


@callback
async def async_setup_entry(
    _: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """
    Set up PandaScore sensors for a configuration entry.


    A set of sensors is created for each team configured in the PandaScore
    integration. The sensors are registered with Home Assistant and linked
    to the shared data update coordinator.

    :param _: The Home Assistant instance. It is unused because the
        coordinator is retrieved from the configuration entry runtime data.
    :param entry: The PandaScore configuration entry containing the configured
        teams and runtime data.
    :param async_add_entities: Callback used to register the created sensor
        entities with Home Assistant.
    :return: ``None``.
    """
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
    """
    Create all sensors associated with a single PandaScore team.


    A Home Assistant device is created for the team, and all sensors belonging
    to that device are initialized with the same device information.

    :param coordinator: The PandaScore data update coordinator used by the
        created sensors.
    :param team: A dictionary containing the PandaScore team information.
    :return: A list of sensor entities associated with the specified team.
    """
    team_id = int(team.get("id") or -1)
    team_slug = team.get("slug", str(team_id))
    game_name = team.get("current_videogame", {}).get("name") or None
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
    """
    Base class for PandaScore team sensors.


    This class provides common initialization and helper functionality for
    all sensors associated with a PandaScore team.

    :param coordinator: The PandaScore data update coordinator providing
        the team's match data.
    :param team: A dictionary containing the PandaScore team information.
    :param team_id: The PandaScore identifier of the team.
    :param team_slug: The unique PandaScore slug of the team.
    :param device_info: The Home Assistant device information associated
        with the team.
    :param sensor_name: The unique name of the sensor type.
    """

    def __init__(
        self,
        coordinator: PandascoreDataUpdateCoordinator,
        team: dict[str, Any],
        team_id: int,
        team_slug: str,
        device_info: DeviceInfo,
        sensor_name: str,
    ) -> None:
        """
        Initialize a PandaScore team sensor.

        :param coordinator: The PandaScore data update coordinator providing
            the sensor data.
        :param team: A dictionary containing the PandaScore team information.
        :param team_id: The PandaScore identifier of the team.
        :param team_slug: The unique PandaScore slug of the team.
        :param device_info: The Home Assistant device information associated
            with the team.
        :param sensor_name: The unique name of the sensor type.
        """
        super().__init__(coordinator, _LOGGER)
        self._team = team
        self._team_id = team_id
        self._attr_unique_id = f"{team_slug}.{sensor_name}"
        self._attr_has_entity_name = True
        self._attr_translation_key = f"{sensor_name}"
        self._attr_device_info = device_info

    def _get_team_data(self) -> TeamData | None:
        """
        Return the latest coordinator data for the configured team.

        :return: The team's :class:`TeamData` instance, or ``None`` if
            no data is currently available for the team.
        """
        return (self.coordinator.data or {}).get(self._team_id)


class PandascoreNameSensor(PandascoreTeamSensorBase):
    """Sensor exposing the configured PandaScore team name."""

    _attr_icon = "mdi:account-group"

    def __init__(self, *args, **kwargs):
        """
        Initialize the team name sensor.

        :param args: Positional arguments forwarded to the base team sensor.
        :param kwargs: Keyword arguments forwarded to the base team sensor.
        """
        super().__init__(*args, sensor_name="name", **kwargs)

    @property
    def native_value(self) -> str | None:
        """
        Return the name of the configured team.

        :return: The team's name, or ``None`` if no name is available.
        """
        return self._team.get("name")


class PandascoreGameSensor(PandascoreTeamSensorBase):
    """Sensor exposing the videogame associated with a PandaScore team."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_icon = "mdi:controller"

    def __init__(self, *args, **kwargs):
        """
        Initialize the team videogame sensor.

        :param args: Positional arguments forwarded to the base team sensor.
        :param kwargs: Keyword arguments forwarded to the base team sensor.
        """
        super().__init__(*args, sensor_name="game", **kwargs)
        self._attr_options = [
            "league-of-legends",
            "rl",
            "valorant",
            "mlbb",
            "starcraft-brood-war",
            "starcraft-2",
            "lol-wild-rift",
            "kog",
            "fifa",
            "r6-siege",
            "cod-mw",
            "pubg",
            "ow",
            "dota-2",
            "cs-go",
        ]

    @property
    def native_value(self) -> str | None:
        """
        Return the normalized videogame slug associated with the team.

        :return: The normalized videogame slug, or ``None`` if no videogame
            is configured for the team.
        """
        return (self._team.get("current_videogame") or {}).get("slug")


class PandascoreMatchesWonSensor(PandascoreTeamSensorBase):
    """Sensor exposing the number of matches won by a PandaScore team."""

    _attr_icon = "mdi:check-network-outline"

    def __init__(self, *args, **kwargs):
        """
        Initialize the matches won sensor.

        :param args: Positional arguments forwarded to the base team sensor.
        :param kwargs: Keyword arguments forwarded to the base team sensor.
        """
        super().__init__(*args, sensor_name="matches_won", **kwargs)

    @property
    def native_value(self) -> int:
        """
        Return the number of matches won by the team.

        :return: The number of finished matches won by the configured team.
            ``0`` is returned when no coordinator data is available.
        """
        data = self._get_team_data()
        if not data:
            return 0
        won = sum(
            1
            for m in data.matches
            if m.winner_id == self._team_id and m.status == "finished"
        )
        return won


class PandascoreMatchesLossSensor(PandascoreTeamSensorBase):
    """Sensor exposing the number of matches lost by a PandaScore team."""

    _attr_icon = "mdi:close-network-outline"

    def __init__(self, *args, **kwargs):
        """
        Initialize the matches loss sensor.

        :param args: Positional arguments forwarded to the base team sensor.
        :param kwargs: Keyword arguments forwarded to the base team sensor.
        """
        super().__init__(*args, sensor_name="matches_loss", **kwargs)

    @property
    def native_value(self) -> int:
        """
        Return the number of matches lost by the team.

        :return: The number of finished matches not won by the configured
            team. ``0`` is returned when no coordinator data is available.
        """
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
    """Sensor exposing the win rate of a PandaScore team."""

    _attr_icon = "mdi:trophy"
    _attr_native_unit_of_measurement = "%"

    def __init__(self, *args, **kwargs):
        """
        Initialize the win rate sensor.

        :param args: Positional arguments forwarded to the base team sensor.
        :param kwargs: Keyword arguments forwarded to the base team sensor.
        """
        super().__init__(*args, sensor_name="win_rate", **kwargs)

    @property
    def native_value(self) -> float | None:
        """
        Return the team's win rate as a percentage.

        The win rate is calculated from finished matches only.

        :return: The team's win rate as a percentage, rounded to two decimal
            places, or ``None`` if the team has not played any finished
            matches.
        """
        data = self._get_team_data()
        if not data:
            return None
        won = sum(
            1
            for m in data.matches
            if m.winner_id == self._team_id and m.status == "finished"
        )
        loss = sum(
            1
            for m in data.matches
            if m.winner_id != self._team_id and m.status == "finished"
        )
        played = won + loss
        win_rate = round(won / played, 4) * 100 if played > 0 else None
        return win_rate


class PandascoreMatchesPlayedSensor(PandascoreTeamSensorBase):
    """Sensor exposing the number of finished matches played by a team."""

    _attr_icon = "mdi:network-outline"

    def __init__(self, *args, **kwargs):
        """
        Initialize the matches played sensor.

        :param args: Positional arguments forwarded to the base team sensor.
        :param kwargs: Keyword arguments forwarded to the base team sensor.
        """
        super().__init__(*args, sensor_name="matches_played", **kwargs)

    @property
    def native_value(self) -> int:
        """
        Return the number of finished matches played by the team.

        :return: The number of finished matches, or ``0`` if no coordinator
            data is available.
        """
        data = self._get_team_data()
        if not data:
            return 0
        return len([m for m in data.matches if m.status == "finished"])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """
        Return the team's previously played matches as state attributes.

        Matches are sorted from the most recent to the oldest match.

        :return: A dictionary containing a ``matches`` attribute with the
            list of formatted past match entries. An empty list is returned
            when no coordinator data is available.
        """
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
    """Sensor exposing the number and details of upcoming matches."""

    _attr_icon = "mdi:help-network-outline"

    def __init__(self, *args, **kwargs):
        """
        Initialize the upcoming matches sensor.

        :param args: Positional arguments forwarded to the base team sensor.
        :param kwargs: Keyword arguments forwarded to the base team sensor.
        """
        super().__init__(*args, sensor_name="upcoming_matches", **kwargs)

    @property
    def native_value(self) -> int:
        """
        Return the number of upcoming matches for the team.

        :return: The number of matches with a ``not_started`` or ``pending``
            status, or ``0`` if no coordinator data is available.
        """
        data = self._get_team_data()
        if not data:
            return 0
        return len([m for m in data.matches if m.status in {"not_started", "pending"}])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """
        Return the team's upcoming matches as state attributes.

        Matches are sorted chronologically from the earliest to the latest
        scheduled match.

        :return: A dictionary containing a ``matches`` attribute with the
            list of formatted upcoming match entries. An empty list is
            returned when no coordinator data is available.
        """
        data = self._get_team_data()
        if not data:
            return {"matches": []}
        upcoming = [m for m in data.matches if m.status in {"not_started", "pending"}]
        upcoming.sort(key=lambda m: m.scheduled_at or m.begin_at or utcnow())
        return {"matches": [build_match_entry(self._team_id, m) for m in upcoming]}


class TeamTrackerSensor(PandascoreTeamSensorBase):
    """
    Sensor exposing the state and data of a team's match tracker.


    The sensor returns the state of the next match when one is available.
    Otherwise, it returns the state of the team's most recent match.

    The match data is exposed through the sensor's extra state attributes
    for use with the Team Tracker card.
    """

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_icon = "mdi:console-network-outline"

    def __init__(self, *args, **kwargs):
        """
        Initialize the team tracker sensor.

        :param args: Positional arguments forwarded to the base team sensor.
        :param kwargs: Keyword arguments forwarded to the base team sensor.
        """
        super().__init__(*args, sensor_name="teamTracker", **kwargs)
        self._attr_options = ["PRE", "IN", "POST"]

    @property
    def native_value(self) -> str | None:
        """
        Return the current match tracker state.

        The next match state is preferred. If no next match is available,
        the state of the last match is returned.

        :return: ``"PRE"``, ``"IN"``, or ``"POST"`` depending on the selected
            match state, or ``None`` if no match data is available.
        """
        data = self._get_team_data()
        if not data:
            return None
        if data.next_match:
            return data.next_match.get("state") or None
        if data.last_match:
            return data.last_match.get("state") or None
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """
        Return match tracker attributes for the selected match.

        The next match data is preferred. If no next match is available,
        the last match data is returned.

        :return: A dictionary containing the match tracker attributes,
            or an empty dictionary if no match data is available.
        """
        data = self._get_team_data()
        if not data:
            return {}
        if data.next_match:
            return data.next_match
        return data.last_match or {}


class PandascoreNextMatchSensor(PandascoreTeamSensorBase):
    """Sensor exposing the state and details of the team's next match."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_icon = "mdi:play-network-outline"

    def __init__(self, *args, **kwargs):
        """
        Initialize the next match sensor.

        :param args: Positional arguments forwarded to the base team sensor.
        :param kwargs: Keyword arguments forwarded to the base team sensor.
        """
        super().__init__(*args, sensor_name="next_match", **kwargs)
        self._attr_options = ["PRE", "IN"]

    @property
    def native_value(self) -> str | None:
        """
        Return the state of the team's next match.

        :return: ``"PRE"`` or ``"IN"`` depending on the current state of
            the next match, or ``None`` if no next match is available.
        """
        data = self._get_team_data()
        if not data:
            return None
        return data.next_match.get("state") or None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """
        Return the details of the team's next match.

        :return: A dictionary containing the next match tracker attributes,
            or an empty dictionary if no next match is available.
        """
        data = self._get_team_data()
        if not data:
            return {}
        return data.next_match or {}


class PandascoreLastMatchSensor(PandascoreTeamSensorBase):
    """Sensor exposing the state and details of the team's last match."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_icon = "mdi:console-network-outline"

    def __init__(self, *args, **kwargs):
        """
        Initialize the last match sensor.

        :param args: Positional arguments forwarded to the base team sensor.
        :param kwargs: Keyword arguments forwarded to the base team sensor.
        """
        super().__init__(*args, sensor_name="last_match", **kwargs)
        self._attr_options = ["POST"]

    @property
    def native_value(self) -> str | None:
        """
        Return the state of the team's last match.

        :return: ``"POST"`` when a last match is available, or ``None``
            if no last match data is available.
        """
        data = self._get_team_data()
        if not data:
            return None
        return data.last_match.get("state") or None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """
        Return the details of the team's last match.

        :return: A dictionary containing the last match tracker attributes,
            or an empty dictionary if no last match is available.
        """
        data = self._get_team_data()
        if not data:
            return {}
        return data.last_match or {}
