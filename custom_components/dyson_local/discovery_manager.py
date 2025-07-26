"""Discovery management for Dyson integration."""

import asyncio
from functools import partial
import logging
from typing import Optional

from libdyson.discovery import DysonDiscovery
from libdyson.dyson_device import DysonDevice

from homeassistant.components.zeroconf import async_get_instance
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .connection import DysonConnectionHandler
from .const import DATA_DEVICES, DATA_DISCOVERY, DOMAIN

_LOGGER = logging.getLogger(__name__)


class DysonDiscoveryManager:
    """Manages Dyson device discovery."""

    def __init__(self, hass: HomeAssistant):
        """Initialize discovery manager."""
        self.hass = hass

    async def connect_with_discovery(
        self,
        entry: ConfigEntry,
        device: DysonDevice,
        coordinator: Optional[DataUpdateCoordinator],
        connection_handler: DysonConnectionHandler,
    ) -> bool:
        """Set up Dyson device with discovery."""
        discovery = await self._ensure_discovery_service()
        setup_entry = connection_handler.create_setup_entry_callback(
            entry, device, coordinator
        )

        # Restore preserved discovered devices (for reload scenarios)
        await self._restore_preserved_devices(discovery)

        # Increment discovery usage count
        self._increment_discovery_count()

        # Register device with discovery service
        await self._register_device_with_discovery(
            discovery, device, setup_entry, entry
        )

        return True

    async def handle_unload_cleanup(self, device: DysonDevice) -> None:
        """Handle discovery cleanup during unload."""
        _LOGGER.debug("Entry uses discovery, handling discovery cleanup")

        self._decrement_discovery_count()

        discovery = self.hass.data[DOMAIN][DATA_DISCOVERY]
        if discovery:
            await self._preserve_discovered_devices(discovery)

            # Only stop discovery service if no other devices are using it
            if self.hass.data[DOMAIN]["discovery_count"] <= 0:
                await self._stop_discovery_service(discovery)
            else:
                _LOGGER.debug(
                    "Discovery service continues running - %d devices still using it",
                    self.hass.data[DOMAIN]["discovery_count"],
                )

    async def _ensure_discovery_service(self) -> DysonDiscovery:
        """Ensure discovery service is running."""
        discovery = self.hass.data[DOMAIN][DATA_DISCOVERY]
        if discovery is None:
            discovery = DysonDiscovery()
            self.hass.data[DOMAIN][DATA_DISCOVERY] = discovery
            _LOGGER.debug("Starting dyson discovery")

            await self.hass.async_add_executor_job(
                discovery.start_discovery, await async_get_instance(self.hass)
            )

            def stop_discovery(_):
                _LOGGER.debug("Stopping dyson discovery")
                discovery.stop_discovery()

            self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_discovery)

        return discovery

    async def _restore_preserved_devices(self, discovery: DysonDiscovery) -> None:
        """Restore preserved discovered devices for reload scenarios."""
        preserved_discovered = self.hass.data[DOMAIN].pop("preserved_discovered", {})
        if preserved_discovered:
            _LOGGER.debug(
                "Restoring preserved discovered devices: %s",
                list(preserved_discovered.keys()),
            )
            with discovery._lock:
                discovery._discovered.update(preserved_discovered)
        else:
            _LOGGER.debug("No preserved discovered devices found to restore")

    def _increment_discovery_count(self) -> None:
        """Increment discovery usage count."""
        if "discovery_count" not in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN]["discovery_count"] = 0
        self.hass.data[DOMAIN]["discovery_count"] += 1
        _LOGGER.debug(
            "Discovery count is now: %d", self.hass.data[DOMAIN]["discovery_count"]
        )

    def _decrement_discovery_count(self) -> None:
        """Decrement discovery usage count."""
        self.hass.data[DOMAIN]["discovery_count"] = max(
            0, self.hass.data[DOMAIN]["discovery_count"] - 1
        )
        _LOGGER.debug(
            "Discovery count after decrement: %d",
            self.hass.data[DOMAIN]["discovery_count"],
        )

    async def _preserve_discovered_devices(self, discovery: DysonDiscovery) -> None:
        """Preserve discovered devices for potential reload."""
        try:
            saved_discovered = {}
            with discovery._lock:
                saved_discovered = discovery._discovered.copy()
                _LOGGER.debug(
                    "Discovery service _discovered contents: %s",
                    dict(discovery._discovered),
                )

            if saved_discovered:
                _LOGGER.debug(
                    "Preserving discovered devices for potential reload: %s",
                    list(saved_discovered.keys()),
                )
                self.hass.data[DOMAIN]["preserved_discovered"] = saved_discovered
            else:
                _LOGGER.debug("No discovered devices to preserve")

        except Exception as e:
            _LOGGER.warning("Error preserving discovery data: %s", e)

    async def _stop_discovery_service(self, discovery: DysonDiscovery) -> None:
        """Stop the discovery service."""
        _LOGGER.debug("Stopping dyson discovery - no more devices using it")
        try:
            await self.hass.async_add_executor_job(discovery.stop_discovery)
            _LOGGER.debug("Successfully stopped discovery service")
        except Exception as e:
            _LOGGER.warning("Error stopping discovery: %s", e)

        self.hass.data[DOMAIN][DATA_DISCOVERY] = None
        self.hass.data[DOMAIN]["discovery_count"] = 0

    async def _register_device_with_discovery(
        self,
        discovery: DysonDiscovery,
        device: DysonDevice,
        setup_entry,
        entry: ConfigEntry,
    ) -> None:
        """Register device with discovery service with enhanced handling."""
        _LOGGER.debug("Registering device %s with discovery service", device.serial)

        # Check what devices are currently discovered
        with discovery._lock:
            discovered_devices = list(discovery._discovered.keys())
            _LOGGER.debug("Currently discovered devices: %s", discovered_devices)

            if device.serial in discovery._discovered:
                discovered_ip = discovery._discovered[device.serial]
                _LOGGER.debug(
                    "Device %s already discovered at %s", device.serial, discovered_ip
                )

        # Register the device with discovery
        await self.hass.async_add_executor_job(
            discovery.register_device, device, setup_entry
        )
        _LOGGER.debug("Registered device %s with discovery", device.serial)

        # Give discovery a moment to potentially call the setup callback
        await asyncio.sleep(0.5)

        # Check if the device was actually connected
        if entry.entry_id not in self.hass.data[DOMAIN][DATA_DEVICES]:
            await self._try_cached_or_preserved_connection(device, setup_entry)

    async def _try_cached_or_preserved_connection(
        self, device: DysonDevice, setup_entry
    ) -> None:
        """Try to connect using cached or preserved IP addresses."""
        # Check if we have a cached IP for this device
        device_ips = self.hass.data[DOMAIN].get("device_ips", {})
        if device.serial in device_ips:
            cached_ip = device_ips[device.serial]
            _LOGGER.debug(
                "Found cached IP %s for device %s, attempting connection",
                cached_ip,
                device.serial,
            )
            try:
                result = await self.hass.async_add_executor_job(
                    partial(setup_entry, cached_ip, is_discovery=True)
                )
                if result:
                    _LOGGER.debug(
                        "Successfully connected device %s via cached IP", device.serial
                    )
                    return
                else:
                    _LOGGER.warning(
                        "Failed to connect device %s via cached IP", device.serial
                    )
            except Exception as e:
                _LOGGER.error(
                    "Error attempting cached IP connection for device %s: %s",
                    device.serial,
                    e,
                )

        # Check if we have preserved discovered data as fallback
        preserved_discovered = self.hass.data[DOMAIN].get("preserved_discovered", {})
        if device.serial in preserved_discovered:
            discovered_ip = preserved_discovered[device.serial]
            _LOGGER.debug(
                "Found device %s at IP %s in preserved discovery data",
                device.serial,
                discovered_ip,
            )
            try:
                result = await self.hass.async_add_executor_job(
                    partial(setup_entry, discovered_ip, is_discovery=True)
                )
                if result:
                    _LOGGER.debug(
                        "Successfully connected device %s via preserved discovery IP",
                        device.serial,
                    )
                    return
                else:
                    _LOGGER.warning(
                        "Failed to connect device %s via preserved discovery IP",
                        device.serial,
                    )
            except Exception as e:
                _LOGGER.error(
                    "Error attempting preserved discovery connection for device %s: %s",
                    device.serial,
                    e,
                )

        _LOGGER.info(
            "Device %s will connect when discovered by the discovery service",
            device.serial,
        )
