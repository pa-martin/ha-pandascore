"""Pandascore integration entrypoint."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntry

from .const import DOMAIN, PLATFORMS
from .coordinator import PandascoreDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Set up the PandaScore integration from a config entry.


    This function creates the data update coordinator, registers the config
    entry update listener, performs the initial data refresh, and forwards
    the config entry setup to all supported platforms.

    :param hass: The Home Assistant instance.
    :param entry: The configuration entry containing the PandaScore settings.
    :return: ``True`` when the integration has been successfully set up.
    """
    coordinator = PandascoreDataUpdateCoordinator(hass, entry)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    entry.runtime_data = {"coordinator": coordinator}

    # Perform first refresh
    await coordinator.async_config_entry_first_refresh()

    # Forward platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """
    Reload the PandaScore integration when its configuration is updated.


    :param hass: The Home Assistant instance.
    :param entry: The updated PandaScore configuration entry.
    :return: ``None``.
    """
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Unload the PandaScore integration from Home Assistant.


    This function unloads all platforms associated with the configuration
    entry.

    :param hass: The Home Assistant instance.
    :param entry: The PandaScore configuration entry to unload.
    :return: ``True`` if all platforms were successfully unloaded,
        otherwise ``False``.
    """
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


@callback
async def async_remove_config_entry_device(
    _: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """
    Determine whether a device can be removed from a config entry.


    A device can be removed when none of its identifiers belong to the
    PandaScore domain and reference data still present in the configuration
    entry runtime data.

    :param _: The Home Assistant instance. It is unused by this function.
    :param config_entry: The PandaScore configuration entry associated with
        the device.
    :param device_entry: The device entry to check for removal.
    :return: ``True`` if the device can be removed, otherwise ``False``.
    """
    return not any(
        identifier
        for identifier in device_entry.identifiers
        if identifier[0] == DOMAIN and identifier[1] in config_entry.runtime_data.data
    )
