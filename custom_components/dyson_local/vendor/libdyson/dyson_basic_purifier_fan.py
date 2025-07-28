"""Dyson Basic Purifier Fan."""

from abc import abstractmethod
from typing import Optional

from .dyson_basic_fan import DysonBasicFan
from .const import ENVIRONMENTAL_FAIL, ENVIRONMENTAL_INIT, ENVIRONMENTAL_OFF


class DysonBasicPurifierFan(DysonBasicFan):
    """Dyson Basic Purifier Fan - basic air purification without advanced environmental sensors."""

    def __init__(self, serial: str, credential: str, device_type: str):
        """Initialize the basic purifier fan device."""
        super().__init__(serial, credential, device_type)
        self._environmental_data = {}

    @property
    def auto_mode(self) -> bool:
        """Return auto mode status."""
        return self._get_field_value(self._status, "auto") == "ON"

    @property
    @abstractmethod
    def oscillation(self) -> bool:
        """Return oscillation status."""

    @property
    def oscillation_status(self) -> bool:
        """Return the status of oscillation."""
        return self._get_field_value(self._status, "oscs") == "ON"

    @property
    def front_airflow(self) -> bool:
        """Return if airflow from front is on."""
        return self._get_field_value(self._status, "fdir") == "ON"

    @property
    def night_mode_speed(self) -> int:
        """Return speed in night mode."""
        value = self._get_field_value(self._status, "nmdv")
        return int(value) if value is not None else 0

    @property
    def carbon_filter_life(self) -> Optional[int]:
        """Return carbon filter life in percentage."""
        filter_life = self._get_field_value(self._status, "cflr")
        if filter_life == "INV" or filter_life is None:
            return None
        return int(filter_life)

    @property
    def hepa_filter_life(self) -> Optional[int]:
        """Return HEPA filter life in percentage."""
        value = self._get_field_value(self._status, "hflr")
        return int(value) if value is not None else None

    @property
    def particulate_matter_2_5(self) -> Optional[int]:
        """Return PM 2.5 in micro grams per cubic meter."""
        pm25 = self._get_environmental_field_value(
            "p25r"
        ) or self._get_environmental_field_value("pm25")
        return int(pm25) if pm25 is not None else None

    @property
    def particulate_matter_10(self) -> Optional[int]:
        """Return PM 10 in micro grams per cubic meter."""
        pm10 = self._get_environmental_field_value(
            "p10r"
        ) or self._get_environmental_field_value("pm10")
        return int(pm10) if pm10 is not None else None

    @property
    def continuous_monitoring(self) -> bool:
        """Return continuous monitoring status."""
        return self._get_field_value(self._status, "rhtm") == "ON"

    def _handle_message(self, payload: dict) -> None:
        """Handle incoming MQTT messages."""
        # Call parent handler for regular state updates
        super()._handle_message(payload)

        # Handle environmental data messages
        if payload["msg"] == "ENVIRONMENTAL-CURRENT-SENSOR-DATA":
            self._environmental_data = payload["data"]
            # Notify listeners of environmental data update
            from .const import MessageType

            for callback in self._callbacks:
                callback(MessageType.ENVIRONMENTAL)

    def _get_environmental_field_value(
        self, field: str, divisor: int = 1
    ) -> Optional[int]:
        """Get environmental field value."""
        # Basic purifiers get environmental data from the environmental payload
        if not hasattr(self, "_environmental_data"):
            self._environmental_data = {}

        value = self._get_field_value(self._environmental_data, field)
        if value == "OFF" or value == "off":
            return ENVIRONMENTAL_OFF
        if value == "INIT":
            return ENVIRONMENTAL_INIT
        if value == "FAIL":
            return ENVIRONMENTAL_FAIL
        if value == "NONE" or value is None:
            return None
        if divisor == 1:
            return int(value)
        return int(float(value) / divisor)

    def _set_configuration(self, **kwargs) -> None:
        """Set device configuration."""
        from .exceptions import DysonNotConnected
        from .utils import mqtt_time
        import json

        if not self.is_connected:
            raise DysonNotConnected
        payload = json.dumps(
            {
                "msg": "STATE-SET",
                "time": mqtt_time(),
                "mode-reason": "LAPP",
                "data": kwargs,
            }
        )
        if self._mqtt_client:
            self._mqtt_client.publish(self._command_topic, payload, 1)

    # NOTE: NO VOC, NO2, humidity, temperature, or CO2 sensors - these don't exist on 438 series

    def _set_speed(self, speed: int) -> None:
        self._set_configuration(fpwr="ON", fnsp=f"{speed:04d}")

    def enable_auto_mode(self) -> None:
        """Turn on auto mode."""
        self._set_configuration(auto="ON")

    def disable_auto_mode(self) -> None:
        """Turn off auto mode."""
        self._set_configuration(auto="OFF")

    def enable_continuous_monitoring(self) -> None:
        """Turn on continuous monitoring."""
        self._set_configuration(rhtm="ON")

    def disable_continuous_monitoring(self) -> None:
        """Turn off continuous monitoring."""
        self._set_configuration(rhtm="OFF")

    def enable_front_airflow(self) -> None:
        """Turn on front airflow."""
        self._set_configuration(fdir="ON")

    def disable_front_airflow(self) -> None:
        """Turn off front airflow."""
        self._set_configuration(fdir="OFF")


class DysonBasicPurifierFanWithOscillation(DysonBasicPurifierFan):
    """Dyson Basic Purifier Fan with standard oscillation (TP04/TP07/TP09/TP11)."""

    @property
    def oscillation(self) -> bool:
        """Return oscillation status."""
        # Seems some devices use OION/OIOF while others uses ON/OFF
        # https://github.com/shenxn/ha-dyson/issues/22
        return self._get_field_value(self._status, "oson") in ["OION", "ON"]

    @property
    def oscillation_angle_low(self) -> int:
        """Return oscillation low angle."""
        value = self._get_field_value(self._status, "osal")
        return int(value) if value is not None else 0

    @property
    def oscillation_angle_high(self) -> int:
        """Return oscillation high angle."""
        value = self._get_field_value(self._status, "osau")
        return int(value) if value is not None else 0

    def enable_oscillation(
        self,
        angle_low: Optional[int] = None,
        angle_high: Optional[int] = None,
    ) -> None:
        """Turn on oscillation."""
        if angle_low is None:
            angle_low = self.oscillation_angle_low
        if angle_high is None:
            angle_high = self.oscillation_angle_high

        if not 5 <= angle_low <= 355:
            raise ValueError("angle_low must be between 5 and 355")
        if not 5 <= angle_high <= 355:
            raise ValueError("angle_high must be between 5 and 355")
        if angle_low >= angle_high:
            raise ValueError("angle_low must be smaller than angle_high")

        self._set_configuration(
            oson="ON",
            osal=f"{angle_low:04d}",
            osau=f"{angle_high:04d}",
            ancp="CUST",
        )

    def disable_oscillation(self) -> None:
        """Turn off oscillation."""
        self._set_configuration(oson="OFF")
