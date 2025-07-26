"""Device management for Dyson integration."""

import asyncio
from datetime import timedelta
import logging
from typing import Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .connection import DysonConnectionHandler
from .const import (
    CONF_CREDENTIAL,
    CONF_DEVICE_TYPE,
    CONF_SERIAL,
    DATA_COORDINATORS,
    DATA_DEVICES,
    DOMAIN,
)
from .discovery_manager import DysonDiscoveryManager
from .utils import get_platforms_for_device
from .vendor.libdyson import Dyson360Eye, Dyson360Heurist, Dyson360VisNav, get_device
from .vendor.libdyson.dyson_device import DysonDevice
from .vendor.libdyson.exceptions import DysonException

_LOGGER = logging.getLogger(__name__)

ENVIRONMENTAL_DATA_UPDATE_INTERVAL = timedelta(seconds=30)


class DysonDeviceManager:
    """Manages Dyson device lifecycle."""

    def __init__(self, hass: HomeAssistant):
        """Initialize device manager."""
        self.hass = hass
        self.connection_handler = DysonConnectionHandler(hass)

    async def async_setup_entry(self, entry: ConfigEntry) -> bool:
        """Set up device from config entry."""
        device = await self._prepare_device(entry)
        coordinator = await self._setup_coordinator(device)

        if entry.data.get(CONF_HOST):
            return await self.connection_handler.connect_with_static_host(
                entry, device, coordinator  # type: ignore[arg-type]
            )
        else:
            discovery_manager = DysonDiscoveryManager(self.hass)
            return await discovery_manager.connect_with_discovery(
                entry, device, coordinator, self.connection_handler  # type: ignore[arg-type]
            )

    async def async_unload_entry(self, entry: ConfigEntry) -> bool:
        """Unload device entry."""
        # Ensure domain data exists
        if DOMAIN not in self.hass.data:
            _LOGGER.warning("Domain data not found during unload")
            return True

        # Ensure sub-dictionaries exist
        if DATA_DEVICES not in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN][DATA_DEVICES] = {}
        if DATA_COORDINATORS not in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN][DATA_COORDINATORS] = {}

        # Check if the entry exists in our data
        if entry.entry_id not in self.hass.data[DOMAIN][DATA_DEVICES]:
            _LOGGER.debug(
                "Entry %s not found in devices data during unload", entry.entry_id
            )
            return True

        device: DysonDevice = self.hass.data[DOMAIN][DATA_DEVICES][entry.entry_id]
        expected_platforms = get_platforms_for_device(device)

        # Unload platforms
        await self._unload_platforms(entry, expected_platforms)

        # Handle discovery cleanup if needed
        if entry.data.get(CONF_HOST) is None:
            discovery_manager = DysonDiscoveryManager(self.hass)
            await discovery_manager.handle_unload_cleanup(device)

        # Clean up coordinator
        await self._cleanup_coordinator(entry, device)

        # Remove from data dictionaries and disconnect device
        await self._cleanup_device(entry, device)

        # Allow time for cleanup
        await asyncio.sleep(0.5)

        _LOGGER.debug("Completed unload for entry %s", entry.entry_id)
        return True

    async def _prepare_device(self, entry: ConfigEntry) -> DysonDevice:
        """Prepare and disconnect device before setup."""
        device = get_device(
            entry.data[CONF_SERIAL],
            entry.data[CONF_CREDENTIAL],
            entry.data[CONF_DEVICE_TYPE],
        )

        if device is None:
            raise ValueError(
                f"Failed to create device for serial {entry.data[CONF_SERIAL]} "
                f"with device type {entry.data[CONF_DEVICE_TYPE]}"
            )

        # Ensure device is disconnected before attempting to connect
        try:
            await self.hass.async_add_executor_job(device.disconnect)
            _LOGGER.debug("Disconnected device %s before setup", device.serial)
            await asyncio.sleep(0.2)
        except Exception as e:
            _LOGGER.debug(
                "Device %s was not connected during setup (expected): %s",
                device.serial,
                e,
            )

        return device

    async def _setup_coordinator(
        self, device: DysonDevice
    ) -> Optional[DataUpdateCoordinator[None]]:
        """Set up coordinator for non-vacuum devices."""
        if isinstance(device, (Dyson360Eye, Dyson360Heurist, Dyson360VisNav)):
            _LOGGER.debug("No coordinator needed for vacuum device %s", device.serial)
            return None

        async def async_update_data() -> None:
            """Poll environmental data from the device."""
            try:
                await self.hass.async_add_executor_job(
                    device.request_environmental_data  # type: ignore[attr-defined]
                )
            except DysonException as err:
                raise UpdateFailed("Failed to request environmental data") from err

        coordinator: DataUpdateCoordinator[None] = DataUpdateCoordinator(
            self.hass,
            _LOGGER,
            name=f"environmental_{device.serial}",
            update_method=async_update_data,
            update_interval=ENVIRONMENTAL_DATA_UPDATE_INTERVAL,
        )
        _LOGGER.debug("Created coordinator for device %s", device.serial)
        return coordinator

    async def _unload_platforms(
        self, entry: ConfigEntry, expected_platforms: list
    ) -> bool:
        """Unload platforms for the device."""
        try:
            platforms_unload_result = (
                await self.hass.config_entries.async_unload_platforms(
                    entry, expected_platforms
                )
            )
            _LOGGER.debug(
                "Platforms unload result for %s: %s",
                entry.entry_id,
                platforms_unload_result,
            )

            if platforms_unload_result:
                await asyncio.sleep(0.5)  # Allow entity cleanup

            return platforms_unload_result

        except ValueError as e:
            if "never loaded" in str(e).lower():
                _LOGGER.debug(
                    "Platforms were never loaded for entry %s", entry.entry_id
                )
                return True
            else:
                _LOGGER.warning(
                    "ValueError during platform unload for entry %s: %s",
                    entry.entry_id,
                    e,
                )
                return True
        except Exception as e:
            _LOGGER.warning(
                "Error unloading platforms for entry %s: %s", entry.entry_id, e
            )
            return True

    async def _cleanup_coordinator(
        self, entry: ConfigEntry, device: DysonDevice
    ) -> None:
        """Clean up coordinator for the device."""
        coordinator = self.hass.data[DOMAIN][DATA_COORDINATORS].pop(
            entry.entry_id, None
        )
        if coordinator:
            try:
                if hasattr(coordinator, "async_shutdown"):
                    await coordinator.async_shutdown()
                _LOGGER.debug(
                    "Successfully shut down coordinator for %s", device.serial
                )
            except Exception as e:
                _LOGGER.warning(
                    "Error shutting down coordinator for %s: %s", device.serial, e
                )

    async def _cleanup_device(self, entry: ConfigEntry, device: DysonDevice) -> None:
        """Clean up device data and disconnect."""
        # Remove from data dictionaries
        self.hass.data[DOMAIN][DATA_DEVICES].pop(entry.entry_id, None)

        # Disconnect device
        try:
            await self.hass.async_add_executor_job(device.disconnect)
            _LOGGER.debug("Successfully disconnected device %s", device.serial)
        except Exception as e:
            _LOGGER.warning("Error disconnecting device %s: %s", device.serial, e)

        await asyncio.sleep(0.1)  # Brief pause for disconnection
