"""Dyson Python library."""

from typing import Optional

from .cloud.device_info import DysonDeviceInfo
from .const import (  # Core MQTT-focused constants
    DEVICE_TYPE_360_EYE,
    DEVICE_TYPE_360_HEURIST,
    DEVICE_TYPE_360_VIS_NAV,
    DEVICE_TYPE_PURE_COOL_LINK,
    DEVICE_TYPE_PURE_COOL_LINK_DESK,
    DEVICE_TYPE_PURE_HOT_COOL_LINK,
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

# Compatibility aliases for backward compatibility with HA integration
# These map to the base classes that the dynamic devices inherit from
from .dyson_basic_purifier_fan import (  # noqa: F401
    DysonBasicPurifierFanWithOscillation as DysonPureCool,
)
from .dyson_basic_purifier_fan_with_heating import (  # noqa: F401
    DysonBasicPurifierFanWithHeating as DysonPureHotCool,
)
from .dyson_basic_purifier_fan_with_humidification import (  # noqa: F401
    DysonBasicPurifierFanWithHumidification as DysonPurifierHumidifyCool,
)
from .dyson_device import DysonDevice
from .dyson_pure_cool_link import DysonPureCoolLink
from .dyson_pure_hot_cool_link import DysonPureHotCoolLink
from .dyson_purifier_big_quiet import DysonBigQuiet  # noqa: F401
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


def get_device_from_info(device_info: DysonDeviceInfo) -> Optional[DysonDevice]:
    """Create a DysonDevice instance from enhanced DysonDeviceInfo.

    This function uses the enhanced MQTT topic detection from DysonDeviceInfo
    to get the correct device type, including proper variant handling.

    This is the recommended way to create devices from cloud account information
    as it automatically handles:
    - mqttRootTopicLevel detection (most accurate)
    - OpenAPI type+variant fields
    - Version field analysis for legacy devices
    - Model field analysis
    - Product type fallback

    Args:
        device_info: Enhanced DysonDeviceInfo instance from cloud account

    Returns:
        DysonDevice instance or None if creation fails
    """
    # Use the enhanced MQTT device type detection
    mqtt_device_type = device_info.get_mqtt_device_type()

    # Create device using the enhanced device type
    return get_device(device_info.serial, device_info.credential, mqtt_device_type)
