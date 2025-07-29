"""Dyson Python library."""

from typing import Optional

from .const import (
    DEVICE_TYPE_360_EYE,
    DEVICE_TYPE_360_HEURIST,
    DEVICE_TYPE_360_VIS_NAV,
    DEVICE_TYPE_PURE_COOL,
    DEVICE_TYPE_PURE_COOL_DESK,
    DEVICE_TYPE_PURE_COOL_LINK,
    DEVICE_TYPE_PURE_COOL_LINK_DESK,
    DEVICE_TYPE_PURE_HOT_COOL,
    DEVICE_TYPE_PURE_HOT_COOL_LINK,
    DEVICE_TYPE_PURE_HUMIDIFY_COOL,
    DEVICE_TYPE_PURIFIER_BIG_QUIET,
    DEVICE_TYPE_PURIFIER_COOL_E,
    DEVICE_TYPE_PURIFIER_COOL_K,
    DEVICE_TYPE_PURIFIER_COOL_M,
    DEVICE_TYPE_PURIFIER_HOT_COOL_E,
    DEVICE_TYPE_PURIFIER_HOT_COOL_K,
    DEVICE_TYPE_PURIFIER_HOT_COOL_M,
    DEVICE_TYPE_PURIFIER_HUMIDIFY_COOL_E,
    DEVICE_TYPE_PURIFIER_HUMIDIFY_COOL_K,
)
from .const import CleaningMode  # noqa: F401
from .const import CleaningType  # noqa: F401
from .const import DEVICE_TYPE_NAMES  # noqa: F401
from .const import HumidifyOscillationMode  # noqa: F401
from .const import MessageType  # noqa: F401
from .const import Tilt  # noqa: F401
from .const import VacuumEyePowerMode  # noqa: F401
from .const import VacuumHeuristPowerMode  # noqa: F401
from .const import VacuumState  # noqa: F401
from .const import VacuumVisNavPowerMode  # noqa: F401
from .const import WaterHardness  # noqa: F401
from .discovery import DysonDiscovery  # noqa: F401
from .dynamic_device_factory import get_device_with_capability_discovery
from .dyson_360_eye import Dyson360Eye
from .dyson_360_heurist import Dyson360Heurist
from .dyson_360_vis_nav import Dyson360VisNav
from .dyson_basic_purifier_fan import DysonBasicPurifierFanWithOscillation
from .dyson_device import DysonDevice
from .dyson_pure_cool import DysonPureCool
from .dyson_pure_cool_link import DysonPureCoolLink
from .dyson_pure_hot_cool import DysonPureHotCool
from .dyson_pure_hot_cool_link import DysonPureHotCoolLink
from .dyson_pure_humidify_cool import DysonPurifierHumidifyCool
from .dyson_purifier_big_quiet import DysonBigQuiet
from .utils import get_mqtt_info_from_wifi_info  # noqa: F401


def get_device(serial: str, credential: str, device_type: str) -> Optional[DysonDevice]:
    """Get a new DysonDevice instance using dynamic capability discovery.

    This method first attempts to create a device using dynamic capability discovery
    by analyzing the device's MQTT capabilities. If that fails or for special cases
    like vacuum robots, it falls back to the traditional static mapping.

    This approach ensures:
    - New Dyson models work automatically without library updates
    - Devices get exactly the features they actually support
    - Backward compatibility is maintained for existing code
    """
    import logging

    _LOGGER = logging.getLogger(__name__)

    _LOGGER.debug("Creating device: serial=%s, device_type=%s", serial, device_type)

    # Special handling for vacuum robots (always use static mapping)
    if device_type in [
        DEVICE_TYPE_360_EYE,
        DEVICE_TYPE_360_HEURIST,
        DEVICE_TYPE_360_VIS_NAV,
    ]:
        return _create_device_static(serial, credential, device_type)

    # Try dynamic capability discovery first for fan/purifier devices
    try:
        _LOGGER.debug(
            "Attempting dynamic capability discovery for device_type: %s", device_type
        )
        dynamic_device = get_device_with_capability_discovery(
            serial, credential, device_type
        )
        if dynamic_device:
            _LOGGER.info(
                "Successfully created device using capability discovery: %s -> %s",
                device_type,
                type(dynamic_device).__name__,
            )
            return dynamic_device
    except Exception as e:
        _LOGGER.warning(
            "Dynamic capability discovery failed for %s: %s. Falling back to static mapping.",
            device_type,
            str(e),
        )

    # Fallback to static mapping
    _LOGGER.debug("Using static device mapping for device_type: %s", device_type)
    return _create_device_static(serial, credential, device_type)


def _create_device_static(
    serial: str, credential: str, device_type: str
) -> Optional[DysonDevice]:
    """Create device using simplified static mapping (fallback only).

    This method now focuses only on:
    1. Vacuum robots (special cases that don't use standard MQTT data)
    2. Legacy Link devices (limited MQTT data)
    3. Backward compatibility for deprecated device type constants

    All other devices should be handled by dynamic capability discovery.
    """
    import logging

    _LOGGER = logging.getLogger(__name__)

    _LOGGER.debug(
        "Static device creation: serial=%s, device_type=%s", serial, device_type
    )

    # Vacuum robots (special cases - always use static mapping)
    if device_type == DEVICE_TYPE_360_EYE:
        _LOGGER.debug("Creating Dyson360Eye robot vacuum")
        return Dyson360Eye(serial, credential)
    if device_type == DEVICE_TYPE_360_HEURIST:
        _LOGGER.debug("Creating Dyson360Heurist robot vacuum")
        return Dyson360Heurist(serial, credential)
    if device_type == DEVICE_TYPE_360_VIS_NAV:
        _LOGGER.debug("Creating Dyson360VisNav robot vacuum")
        return Dyson360VisNav(serial, credential)

    # Legacy Link devices (limited MQTT data - require static mapping)
    if device_type in [DEVICE_TYPE_PURE_COOL_LINK_DESK, DEVICE_TYPE_PURE_COOL_LINK]:
        _LOGGER.debug("Creating DysonPureCoolLink device (legacy)")
        return DysonPureCoolLink(serial, credential, device_type)
    if device_type == DEVICE_TYPE_PURE_HOT_COOL_LINK:
        _LOGGER.debug("Creating DysonPureHotCoolLink device (legacy)")
        return DysonPureHotCoolLink(serial, credential, device_type)

    # For modern devices, use the static mapping but this should be rare
    if device_type in [
        DEVICE_TYPE_PURE_COOL,
        DEVICE_TYPE_PURIFIER_COOL_K,  # 438K - Basic purifier without advanced sensors
        DEVICE_TYPE_PURIFIER_COOL_E,  # 438E - Basic purifier without advanced sensors
        DEVICE_TYPE_PURIFIER_COOL_M,  # 438M - Basic purifier without advanced sensors
    ]:
        _LOGGER.debug(
            "Creating DysonBasicPurifierFanWithOscillation device for 438 series (fallback)"
        )
        return DysonBasicPurifierFanWithOscillation(serial, credential, device_type)
    if device_type in [
        DEVICE_TYPE_PURE_COOL_DESK,
    ]:
        _LOGGER.debug("Creating DysonPureCool device (fallback)")
        return DysonPureCool(serial, credential, device_type)
    if device_type in [
        DEVICE_TYPE_PURE_HOT_COOL,
        DEVICE_TYPE_PURIFIER_HOT_COOL_E,  # Deprecated - backward compatibility
        DEVICE_TYPE_PURIFIER_HOT_COOL_K,  # Deprecated - backward compatibility
        DEVICE_TYPE_PURIFIER_HOT_COOL_M,  # Deprecated - backward compatibility
    ]:
        _LOGGER.debug("Creating DysonPureHotCool device (fallback)")
        return DysonPureHotCool(serial, credential, device_type)
    if device_type in [
        DEVICE_TYPE_PURE_HUMIDIFY_COOL,
        DEVICE_TYPE_PURIFIER_HUMIDIFY_COOL_K,  # Deprecated - backward compatibility
        DEVICE_TYPE_PURIFIER_HUMIDIFY_COOL_E,  # Deprecated - backward compatibility
    ]:
        _LOGGER.debug("Creating DysonPurifierHumidifyCool device (fallback)")
        return DysonPurifierHumidifyCool(serial, credential, device_type)
    if device_type in {
        DEVICE_TYPE_PURIFIER_BIG_QUIET,
    }:
        _LOGGER.debug("Creating DysonBigQuiet device (fallback)")
        return DysonBigQuiet(serial, credential, device_type)

    # All other device types should be handled by dynamic capability discovery
    # This fallback should rarely be used
    _LOGGER.warning(
        "No static mapping available for device_type: %s. Dynamic discovery should have handled this.",
        device_type,
    )

    _LOGGER.error(
        "Unknown device type: %s for serial: %s. No static mapping available.",
        device_type,
        serial,
    )
    return None


def get_device_with_progressive_discovery(
    serial: str, credential: str, device_type: str, hass, entry
) -> Optional[DysonDevice]:
    """Get a device with progressive discovery enabled.

    This function creates a device and sets up progressive discovery monitoring
    if configured to do so. It's a wrapper around get_device_with_capability_discovery
    that handles the Home Assistant integration specifics.
    """
    import logging

    _LOGGER = logging.getLogger(__name__)

    # Check if progressive discovery is enabled
    progressive_enabled = entry.options.get("progressive_discovery", True)

    # Check if we're in a test environment - if progressive discovery is disabled
    # in config, fall back to regular device creation which can be mocked properly
    test_mode = entry.options.get("progressive_discovery", True) is False

    if progressive_enabled and not test_mode:
        _LOGGER.debug(
            "Creating device with progressive discovery enabled for %s", serial
        )
        try:
            # Use the dynamic factory with progressive mode enabled
            device = get_device_with_capability_discovery(
                serial, credential, device_type, progressive_mode=True
            )
            if device:
                # Set up progressive discovery monitoring
                from custom_components.dyson_local.progressive_discovery import (
                    ProgressiveDiscoveryManager,
                )

                discovery_manager = ProgressiveDiscoveryManager(hass, device, entry)
                # Store the discovery manager on the device for later cleanup
                device._progressive_discovery_manager = discovery_manager

                # Start progressive discovery monitoring (will be scheduled)
                import asyncio

                if hasattr(hass, "async_create_task"):
                    hass.async_create_task(discovery_manager.start_monitoring())
                else:
                    # Fallback for testing or unusual environments
                    asyncio.create_task(discovery_manager.start_monitoring())

                return device
        except Exception as e:
            _LOGGER.warning(
                "Progressive discovery failed for %s: %s. Falling back to static mapping.",
                device_type,
                str(e),
            )

    # Fallback to regular device creation
    return get_device(serial, credential, device_type)
