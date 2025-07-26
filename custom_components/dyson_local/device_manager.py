"""Device management for Dyson integration."""

import asyncio
from datetime import timedelta
import logging
from typing import Optional

from libdyson import Dyson360Eye, Dyson360Heurist, Dyson360VisNav, get_device
from libdyson.dyson_device import DysonDevice
from libdyson.exceptions import DysonException, DysonInvalidAuth

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .cloud.const import CONF_AUTH
from .cloud.manager import async_handle_auth_failure
from .connection import DysonConnectionHandler
from .const import (
    CONF_AUTO_DISCOVERY,
    CONF_CLOUD_POLL_INTERVAL,
    CONF_CREDENTIAL,
    CONF_DEVICE_TYPE,
    CONF_ENABLE_POLLING,
    CONF_SERIAL,
    DATA_COORDINATORS,
    DATA_DEVICES,
    DEFAULT_AUTO_DISCOVERY,
    DEFAULT_CLOUD_POLL_INTERVAL,
    DEFAULT_ENABLE_POLLING,
    DOMAIN,
)
from .discovery_manager import DysonDiscoveryManager
from .utils import get_platforms_for_device

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
        coordinator = await self._setup_coordinator(device, entry)

        # Set up cloud polling coordinator if this is a cloud-managed device and auto-discovery is enabled
        if CONF_AUTH in entry.data:
            auto_discovery_enabled = entry.options.get(
                CONF_AUTO_DISCOVERY, DEFAULT_AUTO_DISCOVERY
            )
            if auto_discovery_enabled:
                await self._setup_cloud_coordinator(entry)
            else:
                _LOGGER.debug("Auto-discovery disabled for entry %s", entry.entry_id)

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

        # Clean up cloud coordinator if it exists
        await self._cleanup_cloud_coordinator(entry)

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
        self, device: DysonDevice, entry: ConfigEntry
    ) -> Optional[DataUpdateCoordinator[None]]:
        """Set up coordinator for non-vacuum devices."""
        if isinstance(device, (Dyson360Eye, Dyson360Heurist, Dyson360VisNav)):
            _LOGGER.debug("No coordinator needed for vacuum device %s", device.serial)
            return None

        # Check if polling is enabled
        enable_polling = entry.options.get(CONF_ENABLE_POLLING, DEFAULT_ENABLE_POLLING)

        if not enable_polling:
            _LOGGER.debug("Polling disabled for device %s", device.serial)
            return None

        async def async_update_data() -> None:
            """Poll environmental data from the device."""
            try:
                await self.hass.async_add_executor_job(
                    device.request_environmental_data  # type: ignore[attr-defined]
                )
            except DysonInvalidAuth as err:
                # Handle authentication errors during device polling
                _LOGGER.warning(
                    "Authentication error during device polling for %s: %s",
                    device.serial,
                    err,
                )
                # Check if this is a cloud-configured device that needs reauth
                entry = None
                for config_entry in self.hass.config_entries.async_entries(DOMAIN):
                    if (
                        config_entry.data.get(CONF_SERIAL) == device.serial
                        and CONF_AUTH in config_entry.data
                    ):
                        entry = config_entry
                        break

                if entry:
                    _LOGGER.info(
                        "Triggering reauth flow for cloud device %s due to authentication failure",
                        device.serial,
                    )
                    await async_handle_auth_failure(self.hass, entry)

                raise UpdateFailed(
                    "Authentication failed - reauth flow initiated"
                ) from err
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

    async def _setup_cloud_coordinator(self, entry: ConfigEntry) -> None:
        """Set up cloud polling coordinator for cloud-managed devices."""
        # Get the poll interval from options, with fallback to default
        poll_interval = entry.options.get(
            CONF_CLOUD_POLL_INTERVAL, DEFAULT_CLOUD_POLL_INTERVAL
        )

        async def async_cloud_update() -> None:
            """Poll cloud for device updates and new devices."""
            try:
                # This will check authentication and refresh device list
                from .cloud.manager import async_check_auth_and_refresh_devices

                await async_check_auth_and_refresh_devices(self.hass, entry)
                _LOGGER.debug(
                    "Cloud poll completed successfully for entry %s", entry.entry_id
                )
            except ConfigEntryAuthFailed:
                # This is already handled by the cloud manager
                raise UpdateFailed(
                    "Cloud authentication failed - reauth flow initiated"
                )
            except Exception as err:
                _LOGGER.warning(
                    "Cloud polling failed for entry %s: %s", entry.entry_id, err
                )
                raise UpdateFailed(f"Cloud polling failed: {err}") from err

        # Create cloud coordinator with configurable interval
        cloud_coordinator: DataUpdateCoordinator[None] = DataUpdateCoordinator(
            self.hass,
            _LOGGER,
            name=f"cloud_{entry.entry_id}",
            update_method=async_cloud_update,
            update_interval=timedelta(seconds=poll_interval),
        )

        # Store cloud coordinator separately
        if DOMAIN not in self.hass.data:
            self.hass.data[DOMAIN] = {}
        if "cloud_coordinators" not in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN]["cloud_coordinators"] = {}

        self.hass.data[DOMAIN]["cloud_coordinators"][entry.entry_id] = cloud_coordinator

        # Start the cloud coordinator
        await cloud_coordinator.async_refresh()

        _LOGGER.debug(
            "Created cloud coordinator for entry %s with %d second interval",
            entry.entry_id,
            poll_interval,
        )

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

    async def _cleanup_cloud_coordinator(self, entry: ConfigEntry) -> None:
        """Clean up cloud coordinator for the entry."""
        if DOMAIN in self.hass.data and "cloud_coordinators" in self.hass.data[DOMAIN]:
            cloud_coordinator = self.hass.data[DOMAIN]["cloud_coordinators"].pop(
                entry.entry_id, None
            )
            if cloud_coordinator:
                try:
                    if hasattr(cloud_coordinator, "async_shutdown"):
                        await cloud_coordinator.async_shutdown()
                    _LOGGER.debug(
                        "Successfully shut down cloud coordinator for entry %s",
                        entry.entry_id,
                    )
                except Exception as e:
                    _LOGGER.warning(
                        "Error shutting down cloud coordinator for entry %s: %s",
                        entry.entry_id,
                        e,
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
