"""Support for Dyson devices."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .cloud.const import CONF_REGION
from .cloud.manager import PLATFORMS as CLOUD_PLATFORMS, async_setup_account
from .const import DATA_COORDINATORS, DATA_DEVICES, DATA_DISCOVERY, DOMAIN
from .device_manager import DysonDeviceManager

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    "binary_sensor",
    "button",
    "camera",
    "climate",
    "fan",
    "humidifier",
    "number",
    "select",
    "sensor",
    "switch",
    "vacuum",
]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up Dyson integration."""
    hass.data[DOMAIN] = {
        DATA_DEVICES: {},
        DATA_COORDINATORS: {},
        DATA_DISCOVERY: None,
        "discovery_count": 0,
        "device_ips": {},
    }
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dyson from a config entry."""
    _LOGGER.debug("Setting up entry: %s", entry.entry_id)

    # Handle cloud accounts
    if CONF_REGION in entry.data:
        return await async_setup_account(hass, entry)

    # Handle local devices
    device_manager = DysonDeviceManager(hass)
    return await device_manager.async_setup_entry(entry)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Dyson entry."""
    _LOGGER.debug("Unloading entry: %s", entry.entry_id)

    # Handle cloud accounts
    if CONF_REGION in entry.data:
        unload_ok = await hass.config_entries.async_unload_platforms(
            entry, CLOUD_PLATFORMS
        )
        if unload_ok and entry.entry_id in hass.data[DOMAIN]:
            hass.data[DOMAIN].pop(entry.entry_id)
        return unload_ok

    # Handle local devices
    device_manager = DysonDeviceManager(hass)
    return await device_manager.async_unload_entry(entry)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Reload Dyson entry."""
    _LOGGER.debug("Reloading entry: %s", entry.entry_id)

    unload_result = await async_unload_entry(hass, entry)
    if not unload_result:
        _LOGGER.error("Failed to unload entry %s during reload", entry.entry_id)
        return False

    # Add delay to ensure complete cleanup
    import asyncio

    await asyncio.sleep(1)

    return await async_setup_entry(hass, entry)
