"""Connection handling for Dyson devices."""

import asyncio
from functools import partial
import logging
from typing import Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DATA_COORDINATORS, DATA_DEVICES, DOMAIN
from .utils import get_platforms_for_device
from .vendor.libdyson.dyson_device import DysonDevice
from .vendor.libdyson.exceptions import DysonException

_LOGGER = logging.getLogger(__name__)


class DysonConnectionHandler:
    """Handles device connections."""

    def __init__(self, hass: HomeAssistant):
        """Initialize connection handler."""
        self.hass = hass

    async def connect_with_static_host(
        self,
        entry: ConfigEntry,
        device: DysonDevice,
        coordinator: Optional[DataUpdateCoordinator],
    ) -> bool:
        """Connect device with static host."""

        def setup_entry(host: str, is_discovery: bool = False) -> bool:
            """Set up entry with given host."""
            _LOGGER.debug("setup_entry called for device %s at %s", device.serial, host)

            # Check if device is already connected and disconnect if necessary
            try:
                if hasattr(device, "is_connected") and device.is_connected:
                    _LOGGER.debug(
                        "Device %s already connected, disconnecting first",
                        device.serial,
                    )
                    device.disconnect()
            except Exception as e:
                _LOGGER.debug(
                    "Error checking/disconnecting device %s: %s", device.serial, e
                )

            try:
                device.connect(host)
                _LOGGER.debug(
                    "Successfully connected to device %s at %s", device.serial, host
                )

                # Cache the IP address for this device
                if is_discovery and host:
                    if "device_ips" not in self.hass.data[DOMAIN]:
                        self.hass.data[DOMAIN]["device_ips"] = {}
                    self.hass.data[DOMAIN]["device_ips"][device.serial] = host
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
                _LOGGER.error(
                    "Failed to connect to device %s at %s during setup: %s",
                    device.serial,
                    host,
                    str(e),
                )
                raise ConfigEntryNotReady from e

            # Store device and coordinator data
            self.hass.data[DOMAIN][DATA_DEVICES][entry.entry_id] = device
            self.hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id] = coordinator
            _LOGGER.debug(
                "Stored device %s and coordinator in hass.data", device.serial
            )

            # Set up platforms
            return self._setup_platforms(entry, device, is_discovery)

        host = entry.data.get(CONF_HOST)
        if host:
            _LOGGER.debug(
                "Setting up device %s with static host: %s", device.serial, host
            )
            result = await self.hass.async_add_executor_job(
                partial(setup_entry, host, is_discovery=False)
            )
            if not result:
                _LOGGER.error(
                    "Failed to set up device %s with static host", device.serial
                )
                raise ConfigEntryNotReady

        return True

    def _setup_platforms(
        self, entry: ConfigEntry, device: DysonDevice, is_discovery: bool
    ) -> bool:
        """Set up platforms for the device."""
        try:
            platforms = get_platforms_for_device(device)
            _LOGGER.debug("Setting up platforms for %s: %s", device.serial, platforms)

            asyncio.run_coroutine_threadsafe(
                self.hass.config_entries.async_forward_entry_setups(entry, platforms),
                self.hass.loop,
            ).result()

            _LOGGER.debug("Successfully set up platforms for %s", device.serial)
            return True

        except Exception as e:
            _LOGGER.error(
                "Failed to set up platforms for %s: %s", device.serial, str(e)
            )

            # Clean up on platform setup failure
            self.hass.data[DOMAIN][DATA_DEVICES].pop(entry.entry_id, None)
            self.hass.data[DOMAIN][DATA_COORDINATORS].pop(entry.entry_id, None)

            try:
                device.disconnect()
            except Exception:
                pass

            if not is_discovery:
                raise ConfigEntryNotReady from e
            return False

    def create_setup_entry_callback(
        self,
        entry: ConfigEntry,
        device: DysonDevice,
        coordinator: Optional[DataUpdateCoordinator],
    ):
        """Create a setup entry callback for discovery."""

        def setup_entry(host: str, is_discovery: bool = True) -> bool:
            """Set up entry callback for discovery."""
            return asyncio.run_coroutine_threadsafe(
                self._async_setup_entry_callback(
                    entry, device, coordinator, host, is_discovery
                ),
                self.hass.loop,
            ).result()

        return setup_entry

    async def _async_setup_entry_callback(
        self,
        entry: ConfigEntry,
        device: DysonDevice,
        coordinator: Optional[DataUpdateCoordinator],
        host: str,
        is_discovery: bool,
    ) -> bool:
        """Async setup entry callback for discovery."""
        _LOGGER.debug(
            "setup_entry called for device %s at %s (discovery: %s)",
            device.serial,
            host,
            is_discovery,
        )

        # Check if device is already connected and disconnect if necessary
        try:
            if hasattr(device, "is_connected") and device.is_connected:
                _LOGGER.debug(
                    "Device %s already connected, disconnecting first", device.serial
                )
                await self.hass.async_add_executor_job(device.disconnect)
        except Exception as e:
            _LOGGER.debug(
                "Error checking/disconnecting device %s: %s", device.serial, e
            )

        try:
            await self.hass.async_add_executor_job(device.connect, host)
            _LOGGER.debug(
                "Successfully connected to device %s at %s", device.serial, host
            )

            # Cache the IP address for this device
            if is_discovery and host:
                if "device_ips" not in self.hass.data[DOMAIN]:
                    self.hass.data[DOMAIN]["device_ips"] = {}
                self.hass.data[DOMAIN]["device_ips"][device.serial] = host
                _LOGGER.debug("Cached IP %s for device %s", host, device.serial)

        except DysonException as e:
            _LOGGER.error(
                "Failed to connect to device %s at %s: %s", device.serial, host, str(e)
            )
            return False

        # Store device and coordinator data
        self.hass.data[DOMAIN][DATA_DEVICES][entry.entry_id] = device
        self.hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id] = coordinator
        _LOGGER.debug("Stored device %s and coordinator in hass.data", device.serial)

        # Set up platforms
        try:
            platforms = get_platforms_for_device(device)
            _LOGGER.debug("Setting up platforms for %s: %s", device.serial, platforms)

            await self.hass.config_entries.async_forward_entry_setups(entry, platforms)
            _LOGGER.debug("Successfully set up platforms for %s", device.serial)
            return True

        except Exception as e:
            _LOGGER.error(
                "Failed to set up platforms for %s: %s", device.serial, str(e)
            )

            # Clean up on platform setup failure
            self.hass.data[DOMAIN][DATA_DEVICES].pop(entry.entry_id, None)
            self.hass.data[DOMAIN][DATA_COORDINATORS].pop(entry.entry_id, None)

            try:
                await self.hass.async_add_executor_job(device.disconnect)
            except Exception:
                pass

            return False
