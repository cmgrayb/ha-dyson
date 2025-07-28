"""Utilities for Dyson Local."""

from typing import Any, List, Optional

from homeassistant.const import STATE_OFF

from .vendor.libdyson import Dyson360Eye, Dyson360Heurist, Dyson360VisNav
from .vendor.libdyson.const import (
    ENVIRONMENTAL_FAIL,
    ENVIRONMENTAL_INIT,
    ENVIRONMENTAL_OFF,
)
from .vendor.libdyson.dyson_device import DysonDevice

STATE_INIT = "init"
STATE_FAIL = "fail"


class environmental_property(property):
    """Environmental status property."""

    def __get__(self, obj: Any, type: Optional[type] = None) -> Any:
        """Get environmental property value."""
        value = super().__get__(obj, type)
        if value == ENVIRONMENTAL_OFF:
            return STATE_OFF
        elif value == ENVIRONMENTAL_INIT:
            return STATE_INIT
        elif value == ENVIRONMENTAL_FAIL:
            return STATE_FAIL
        return value


def get_platforms_for_device(device: DysonDevice) -> List[str]:
    """Get the platforms that should be loaded for a device."""
    if isinstance(device, (Dyson360Eye, Dyson360Heurist, Dyson360VisNav)):
        return ["binary_sensor", "sensor", "vacuum"]

    platforms = ["fan", "select", "sensor", "switch"]

    # Check for heating capability (climate platform)
    if hasattr(device, "heat_target") or hasattr(device, "heat_mode"):
        platforms.append("climate")

    # Check for legacy Link device (additional platforms)
    if hasattr(device, "device_type") and device.device_type in ["455", "475", "469"]:
        platforms.append("binary_sensor")
        if device.device_type == "455":  # HP02 (Pure Hot+Cool Link)
            platforms.append("climate")

    # Check for humidification capability
    if hasattr(device, "humidification") or hasattr(device, "target_humidity"):
        platforms.append("humidifier")

    # Check for filter monitoring (button platform)
    if (
        hasattr(device, "filter_life")
        or hasattr(device, "carbon_filter_life")
        or hasattr(device, "hepa_filter_life")
    ):
        platforms.append("button")

    # Add number platform for devices that support oscillation angle control
    if (
        hasattr(device, "oscillation_angle_low")
        and hasattr(device, "oscillation_angle_high")
        and hasattr(device, "enable_oscillation")
    ):
        platforms.append("number")

    return platforms
