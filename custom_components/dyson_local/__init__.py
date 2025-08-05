"""Support for Dyson devices."""

import logging
from typing import List, Optional

from homeassistant.components.zeroconf import async_get_instance
from homeassistant.config_entries import SOURCE_DISCOVERY, ConfigEntry
from homeassistant.const import CONF_HOST, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .cloud.const import CONF_AUTH, CONF_REGION, DATA_ACCOUNT, DATA_DEVICES
from .const import (
    CONF_CREDENTIAL,
    CONF_DEVICE_TYPE,
    CONF_SERIAL,
    DATA_COORDINATORS,
    DATA_DEVICES,
    DATA_DISCOVERY,
    DOMAIN,
)
from .vendor.libdyson import (
    Dyson360Eye,
    Dyson360Heurist,
    Dyson360VisNav,
    DysonPureHotCool,
    DysonPureHotCoolLink,
    DysonPurifierHumidifyCool,
    MessageType,
    get_device,
)
from .vendor.libdyson.cloud import DysonAccount, DysonAccountCN
from .vendor.libdyson.discovery import DysonDiscovery
from .vendor.libdyson.dyson_device import DysonDevice
from .vendor.libdyson.exceptions import (
    DysonException,
    DysonInvalidAuth,
    DysonLoginFailure,
    DysonNetworkError,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["camera"]


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


async def async_setup_account(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a MyDyson Account."""
    _LOGGER.debug("Setting up MyDyson Account for region: %s", entry.data[CONF_REGION])

    if entry.data[CONF_REGION] == "CN":
        account = DysonAccountCN(entry.data[CONF_AUTH])
    else:
        account = DysonAccount(entry.data[CONF_AUTH])
    try:
        _LOGGER.debug("Calling account.devices() to get device list")
        devices = await hass.async_add_executor_job(account.devices)
        _LOGGER.debug("Retrieved %d devices from cloud", len(devices))
    except DysonNetworkError:
        _LOGGER.error("Cannot connect to Dyson cloud service.")
        raise ConfigEntryNotReady
    except DysonInvalidAuth:
        _LOGGER.error("Invalid authentication credentials for Dyson cloud service.")
        raise ConfigEntryNotReady
    except Exception as e:
        _LOGGER.error("Unexpected error retrieving devices: %s", str(e))
        raise ConfigEntryNotReady

    _LOGGER.debug("Starting device discovery flows for %d devices", len(devices))
    for device in devices:
        _LOGGER.debug("Creating discovery flow for device: %s (ProductType: %s)",
                      device.name, device.product_type)
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_DISCOVERY},
                data=device,
            )
        )

    hass.data[DOMAIN][entry.entry_id] = {
        DATA_ACCOUNT: account,
        DATA_DEVICES: devices,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dyson from a config entry."""
    _LOGGER.debug("Setting up entry: %s", entry.entry_id)

    # Handle cloud accounts
    if CONF_REGION in entry.data:
        return await async_setup_account(hass, entry)

    device = get_device(
        entry.data[CONF_SERIAL],
        entry.data[CONF_CREDENTIAL],
        entry.data[CONF_DEVICE_TYPE],
    )

    # Ensure device is disconnected before attempting to connect
    # This is important for reload scenarios
    try:
        await hass.async_add_executor_job(device.disconnect)
        _LOGGER.debug("Disconnected device %s before setup", device.serial)
        # Give a moment for the disconnection to complete
        await asyncio.sleep(0.2)
    except Exception as e:
        # Device might not have been connected, which is fine
        _LOGGER.debug("Device %s was not connected during setup (expected): %s", device.serial, e)

    if (not isinstance(device, Dyson360Eye)
            and not isinstance(device, Dyson360Heurist)
            and not isinstance(device, Dyson360VisNav)):
        # Set up coordinator
        async def async_update_data():
            """Poll environmental data from the device."""
            try:
                await hass.async_add_executor_job(device.request_environmental_data)
            except DysonException as err:
                raise UpdateFailed("Failed to request environmental data") from err

        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=f"environmental_{device.serial}",
            update_method=async_update_data,
            update_interval=ENVIRONMENTAL_DATA_UPDATE_INTERVAL,
            config_entry=entry,
        )
        _LOGGER.debug("Created coordinator for device %s", device.serial)
    else:
        coordinator = None
        _LOGGER.debug("No coordinator needed for vacuum device %s", device.serial)

    def setup_entry(host: str, is_discovery: bool = True) -> bool:
        _LOGGER.debug("setup_entry called for device %s at %s (discovery: %s)", device.serial, host, is_discovery)

        # Check if device is already connected and disconnect if necessary
        try:
            if hasattr(device, 'is_connected') and device.is_connected:
                _LOGGER.debug("Device %s already connected, disconnecting first", device.serial)
                device.disconnect()
        except Exception as e:
            _LOGGER.debug("Error checking/disconnecting device %s: %s", device.serial, e)

        try:
            device.connect(host)
            _LOGGER.debug("Successfully connected to device %s at %s", device.serial, host)

            # Cache the IP address for this device for future use
            if is_discovery and host:
                if "device_ips" not in hass.data[DOMAIN]:
                    hass.data[DOMAIN]["device_ips"] = {}
                hass.data[DOMAIN]["device_ips"][device.serial] = host
                _LOGGER.debug("Cached IP %s for device %s", host, device.serial)

        except DysonException as e:
            if is_discovery:
                _LOGGER.error(
                    "Failed to connect to device %s at %s: %s",
                    device.serial,
                    host,
                    str(e),
                )
                return False
            _LOGGER.error("Failed to connect to device %s at %s during setup: %s", device.serial, host, str(e))
            raise ConfigEntryNotReady from e

        # Store device and coordinator data
        hass.data[DOMAIN][DATA_DEVICES][entry.entry_id] = device
        hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id] = coordinator
        _LOGGER.debug("Stored device %s and coordinator in hass.data", device.serial)

        # Set up platforms
        try:
            platforms = _async_get_platforms(device)
            _LOGGER.debug("Setting up platforms for %s: %s", device.serial, platforms)
            asyncio.run_coroutine_threadsafe(
                hass.config_entries.async_forward_entry_setups(entry, platforms), hass.loop
            ).result()
            _LOGGER.debug("Successfully set up platforms for %s", device.serial)
        except Exception as e:
            _LOGGER.error("Failed to set up platforms for %s: %s", device.serial, str(e))
            # Clean up on platform setup failure
            hass.data[DOMAIN][DATA_DEVICES].pop(entry.entry_id, None)
            hass.data[DOMAIN][DATA_COORDINATORS].pop(entry.entry_id, None)
            try:
                device.disconnect()
            except Exception:
                pass
            if not is_discovery:
                raise ConfigEntryNotReady from e
            return False

        _LOGGER.debug("setup_entry completed successfully for device %s", device.serial)
        return True

    host = entry.data.get(CONF_HOST)
    if host:
        _LOGGER.debug("Setting up device %s with static host: %s", device.serial, host)
        result = await hass.async_add_executor_job(
            partial(setup_entry, host, is_discovery=False)
        )
        if not result:
            _LOGGER.error("Failed to set up device %s with static host", device.serial)
            raise ConfigEntryNotReady
    else:
        _LOGGER.debug("Setting up device %s with discovery", device.serial)
        discovery = hass.data[DOMAIN][DATA_DISCOVERY]
        if discovery is None:
            discovery = DysonDiscovery()
            hass.data[DOMAIN][DATA_DISCOVERY] = discovery
            _LOGGER.debug("Starting dyson discovery")
            discovery.start_discovery(await async_get_instance(hass))

            def stop_discovery(_):
                _LOGGER.debug("Stopping dyson discovery")
                discovery.stop_discovery()

            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_discovery)

        # Always check for and restore preserved discovered devices (for reload scenarios)
        # This should happen whether discovery is new or existing
        preserved_discovered = hass.data[DOMAIN].pop("preserved_discovered", {})
        if preserved_discovered:
            _LOGGER.debug("Restoring preserved discovered devices: %s", list(preserved_discovered.keys()))
            with discovery._lock:
                # Merge preserved devices with any currently discovered devices
                discovery._discovered.update(preserved_discovered)
        else:
            _LOGGER.debug("No preserved discovered devices found to restore")

        # Increment discovery usage count
        if "discovery_count" not in hass.data[DOMAIN]:
            hass.data[DOMAIN]["discovery_count"] = 0
        hass.data[DOMAIN]["discovery_count"] += 1
        _LOGGER.debug("Discovery count is now: %d", hass.data[DOMAIN]["discovery_count"])

        # Register device with discovery service with enhanced handling
        await _async_register_device_with_discovery(hass, discovery, device, setup_entry, entry)
        _LOGGER.debug("Device %s registration with discovery completed", device.serial)

    _LOGGER.debug("Successfully completed setup for entry: %s", entry.entry_id)

    # For discovery-based devices, we might not have immediate connection
    # The device will connect when discovered, so don't fail here
    if entry.data.get(CONF_HOST) and entry.entry_id not in hass.data[DOMAIN][DATA_DEVICES]:
        # Only fail for static host devices that should have connected immediately
        _LOGGER.error("Device setup verification failed - device %s not found in data after setup", device.serial)
        raise ConfigEntryNotReady

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Dyson entry."""
    _LOGGER.debug("Unloading entry: %s", entry.entry_id)

    # Handle cloud accounts
    if CONF_REGION in entry.data:
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
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
