"""Dyson Basic Fan device."""

import json
import logging
from typing import Any, Dict, Optional

from .dyson_device import DysonDevice
from .exceptions import DysonNotConnected
from .utils import mqtt_time

_LOGGER = logging.getLogger(__name__)


class DysonBasicFan(DysonDevice):
    """Basic Dyson fan with essential fan controls only.

    This class provides the minimal functionality present in all Dyson fans:
    - Power control (on/off)
    - Speed control
    - Basic oscillation
    - Night mode

    It does NOT include:
    - Auto mode (requires air quality sensors)
    - Air quality monitoring
    - Filter management
    - Environmental sensors
    """

    def __init__(self, serial: str, credential: str, device_type: str):
        """Initialize the basic fan device."""
        super().__init__(serial, credential)
        self._device_type = device_type

    @property
    def device_type(self) -> str:
        """Device type."""
        return self._device_type

    @property
    def _status_topic(self) -> str:
        """MQTT status topic."""
        return f"{self.device_type}/{self._serial}/status/current"

    @staticmethod
    def _get_field_value(state: Dict[str, Any], field: str):
        """Get field value from state dictionary."""
        try:
            return state[field][1] if isinstance(state[field], list) else state[field]
        except (KeyError, TypeError, IndexError):
            return None

    def _set_configuration(self, **kwargs: Any) -> None:
        """Send configuration to device."""
        if not self.is_connected:
            _LOGGER.debug(
                "Device %s not connected, cannot send configuration", self.serial
            )
            raise DysonNotConnected
        payload = json.dumps(
            {
                "msg": "STATE-SET",
                "time": mqtt_time(),
                "mode-reason": "LAPP",
                "data": kwargs,
            }
        )
        _LOGGER.debug("Sending configuration to device %s: %s", self.serial, payload)
        self._mqtt_client.publish(self._command_topic, payload, 1)  # type: ignore
        _LOGGER.debug("Configuration sent to topic %s", self._command_topic)

    @property
    def is_on(self) -> bool:
        """Return if the device is on."""
        return self._get_field_value(self._status, "fpwr") == "ON"

    @property
    def fan_state(self) -> bool:
        """Return if the fan is running."""
        return self._get_field_value(self._status, "fnst") == "FAN"

    @property
    def speed(self) -> Optional[int]:
        """Return fan speed."""
        speed = self._get_field_value(self._status, "fnsp")
        if speed == "AUTO" or speed is None:
            return None
        return int(speed)

    @property
    def oscillation(self) -> bool:
        """Return oscillation status."""
        return self._get_field_value(self._status, "oson") == "ON"

    @property
    def night_mode(self) -> bool:
        """Return night mode status."""
        return self._get_field_value(self._status, "nmod") == "ON"

    @property
    def night_mode_speed(self) -> int:
        """Return speed in night mode."""
        nmdv = self._get_field_value(self._status, "nmdv")
        return int(nmdv) if nmdv is not None else 0

    @property
    def error_code(self) -> Optional[str]:
        """Return error code."""
        return self._get_field_value(self._status, "ercd")

    @property
    def warning_code(self) -> Optional[str]:
        """Return warning code."""
        return self._get_field_value(self._status, "wacd")

    def turn_on(self) -> None:
        """Turn on the device."""
        _LOGGER.debug("turn_on() called for device %s", self.serial)
        self._set_configuration(fpwr="ON")

    def turn_off(self) -> None:
        """Turn off the device."""
        _LOGGER.debug("turn_off() called for device %s", self.serial)
        self._set_configuration(fpwr="OFF")

    def set_speed(self, speed: int) -> None:
        """Set manual speed."""
        if not 1 <= speed <= 10:
            raise ValueError(f"Invalid speed {speed}. Must be between 1 and 10.")
        _LOGGER.debug("set_speed(%d) called for device %s", speed, self.serial)
        self._set_configuration(fpwr="ON", fnsp=f"{speed:04d}")

    def enable_oscillation(self) -> None:
        """Turn on oscillation."""
        _LOGGER.debug("enable_oscillation() called for device %s", self.serial)
        self._set_configuration(oson="ON")

    def disable_oscillation(self) -> None:
        """Turn off oscillation."""
        _LOGGER.debug("disable_oscillation() called for device %s", self.serial)
        self._set_configuration(oson="OFF")

    def enable_night_mode(self) -> None:
        """Turn on night mode."""
        _LOGGER.debug("enable_night_mode() called for device %s", self.serial)
        self._set_configuration(nmod="ON")

    def disable_night_mode(self) -> None:
        """Turn off night mode."""
        _LOGGER.debug("disable_night_mode() called for device %s", self.serial)
        self._set_configuration(nmod="OFF")

    def _update_status(self, payload: dict) -> None:
        """Update device status from MQTT payload."""
        self._status = payload["product-state"]

    def _request_first_data(self) -> bool:
        """Request and wait for first data."""
        self.request_current_status()
        status_available = self._status_data_available.wait(
            timeout=30
        )  # 30 second timeout
        return status_available
