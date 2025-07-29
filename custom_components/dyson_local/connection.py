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
        """Connect device with static host, fallback to discovery if host unreachable."""

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

                # Request immediate status update (step 4 of desired flow)
                try:
                    _LOGGER.debug(
                        "Requesting immediate status for device %s", device.serial
                    )
                    device.request_current_status()
                    _LOGGER.debug(
                        "Successfully requested current state for device %s",
                        device.serial,
                    )

                    # Also request environmental data like the mobile app does
                    if hasattr(device, "request_environmental_data"):
                        device.request_environmental_data()
                        _LOGGER.debug(
                            "Successfully requested environmental data for device %s",
                            device.serial,
                        )

                except Exception as e:
                    _LOGGER.warning(
                        "Failed to request immediate status for device %s: %s",
                        device.serial,
                        e,
                    )

                # Cache the IP address for this device (update if different)
                if host:
                    if "device_ips" not in self.hass.data[DOMAIN]:
                        self.hass.data[DOMAIN]["device_ips"] = {}
                    old_ip = self.hass.data[DOMAIN]["device_ips"].get(device.serial)
                    if old_ip != host:
                        self.hass.data[DOMAIN]["device_ips"][device.serial] = host
                        _LOGGER.debug(
                            "Updated cached IP %s for device %s (was %s)",
                            host,
                            device.serial,
                            old_ip,
                        )
                    else:
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
            try:
                result = await self.hass.async_add_executor_job(
                    partial(setup_entry, host, is_discovery=False)
                )
                if result:
                    return True
                else:
                    _LOGGER.error(
                        "Failed to set up device %s with static host", device.serial
                    )
                    raise ConfigEntryNotReady
            except ConfigEntryNotReady:
                # Static host failed, try Zeroconf discovery first, then cloud API as last resort
                _LOGGER.warning(
                    "Static host %s failed for device %s, attempting Zeroconf discovery",
                    host,
                    device.serial,
                )
                try:
                    return await self._try_zeroconf_discovery(
                        entry, device, coordinator
                    )
                except Exception as e:
                    _LOGGER.warning(
                        "Zeroconf discovery failed for device %s: %s, trying cloud API query",
                        device.serial,
                        e,
                    )
                    return await self._try_cloud_api_refresh(entry, device, coordinator)

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

    async def _try_zeroconf_discovery(
        self,
        entry: ConfigEntry,
        device: DysonDevice,
        coordinator: Optional[DataUpdateCoordinator],
    ) -> bool:
        """Try to find device using Zeroconf/mDNS discovery."""
        from .discovery_manager import DysonDiscoveryManager

        _LOGGER.debug("Attempting Zeroconf discovery for device %s", device.serial)

        discovery_manager = DysonDiscoveryManager(self.hass)
        return await discovery_manager.connect_with_discovery(
            entry, device, coordinator, self
        )

    async def _try_cloud_api_refresh(
        self,
        entry: ConfigEntry,
        device: DysonDevice,
        coordinator: Optional[DataUpdateCoordinator],
    ) -> bool:
        """Try to get new IP from cloud API and reconnect."""
        from .cloud.const import CONF_AUTH, CONF_REGION
        from .vendor.libdyson.cloud import DysonAccount, DysonAccountCN
        from .vendor.libdyson.exceptions import DysonInvalidAuth, DysonNetworkError

        _LOGGER.debug("Attempting cloud API refresh for device %s", device.serial)

        # Find the cloud account entry for this device
        cloud_entry = None
        for config_entry in self.hass.config_entries.async_entries(DOMAIN):
            if CONF_AUTH in config_entry.data:
                # Check if this cloud account has our device
                if config_entry.entry_id in self.hass.data.get(DOMAIN, {}):
                    account_data = self.hass.data[DOMAIN][config_entry.entry_id]
                    devices = account_data.get("devices", [])
                    if any(d.serial == device.serial for d in devices):
                        cloud_entry = config_entry
                        break

        if not cloud_entry:
            _LOGGER.warning(
                "No cloud account found for device %s, cannot refresh IP", device.serial
            )
            raise ConfigEntryNotReady("No cloud account available for IP refresh")

        try:
            # Get account instance
            region = cloud_entry.data[CONF_REGION]
            auth_info = cloud_entry.data[CONF_AUTH]

            if region == "CN":
                account = DysonAccountCN(auth_info)
            else:
                account = DysonAccount(auth_info)

            # Refresh devices from cloud
            devices = await self.hass.async_add_executor_job(account.devices)

            # Find our device in the refreshed list
            device_info = None
            for d in devices:
                if d.serial == device.serial:
                    device_info = d
                    break

            if not device_info:
                _LOGGER.error("Device %s not found in cloud account", device.serial)
                raise ConfigEntryNotReady("Device not found in cloud account")

            # Check if device has IP information
            if not hasattr(device_info, "ip") or not device_info.ip:
                _LOGGER.warning(
                    "Device %s has no IP information in cloud data", device.serial
                )
                raise ConfigEntryNotReady("No IP information available from cloud")

            new_ip = device_info.ip
            _LOGGER.info(
                "Cloud API provided new IP %s for device %s", new_ip, device.serial
            )

            # Update config entry with new IP
            new_data = {**entry.data}
            new_data[CONF_HOST] = new_ip
            self.hass.config_entries.async_update_entry(entry, data=new_data)

            # Try connecting with new IP
            return await self.hass.async_add_executor_job(
                partial(self._setup_entry_with_host, new_ip, device, coordinator, entry)
            )

        except (DysonNetworkError, DysonInvalidAuth) as e:
            _LOGGER.error("Cloud API failed for device %s: %s", device.serial, e)
            raise ConfigEntryNotReady("Cloud API authentication failed") from e
        except Exception as e:
            _LOGGER.error(
                "Unexpected error during cloud API refresh for device %s: %s",
                device.serial,
                e,
            )
            raise ConfigEntryNotReady("Cloud API refresh failed") from e

    def _setup_entry_with_host(
        self,
        host: str,
        device: DysonDevice,
        coordinator: Optional[DataUpdateCoordinator],
        entry: ConfigEntry,
    ) -> bool:
        """Set up entry with a specific host (used by cloud API refresh)."""
        _LOGGER.debug(
            "Setting up device %s with refreshed host %s", device.serial, host
        )

        try:
            if hasattr(device, "is_connected") and device.is_connected:
                device.disconnect()
        except Exception as e:
            _LOGGER.debug("Error disconnecting device %s: %s", device.serial, e)

        try:
            device.connect(host)
            _LOGGER.debug(
                "Successfully connected to device %s at %s", device.serial, host
            )

            # Request immediate status
            try:
                device.request_current_status()
                if hasattr(device, "request_environmental_data"):
                    device.request_environmental_data()
                _LOGGER.debug(
                    "Successfully requested status for device %s", device.serial
                )
            except Exception as e:
                _LOGGER.warning(
                    "Failed to request status for device %s: %s", device.serial, e
                )

            # Cache the new IP
            if "device_ips" not in self.hass.data[DOMAIN]:
                self.hass.data[DOMAIN]["device_ips"] = {}
            self.hass.data[DOMAIN]["device_ips"][device.serial] = host
            _LOGGER.debug("Cached new IP %s for device %s", host, device.serial)

            # Store device data
            self.hass.data[DOMAIN][DATA_DEVICES][entry.entry_id] = device
            self.hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id] = coordinator

            # Set up platforms
            return self._setup_platforms(entry, device, is_discovery=False)

        except DysonException as e:
            _LOGGER.error(
                "Failed to connect to device %s at refreshed host %s: %s",
                device.serial,
                host,
                e,
            )
            raise ConfigEntryNotReady from e
