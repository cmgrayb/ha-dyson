"""Dyson Basic Purifier Fan with Humidification device."""

from typing import Optional

from .const import HumidifyOscillationMode, WaterHardness
from .dyson_basic_purifier_fan import DysonBasicPurifierFanWithOscillation

WATER_HARDNESS_ENUM_TO_STR = {
    WaterHardness.SOFT: "2025",
    WaterHardness.MEDIUM: "1350",
    WaterHardness.HARD: "0675",
}
WATER_HARDNESS_STR_TO_ENUM = {
    str_: enum for enum, str_ in WATER_HARDNESS_ENUM_TO_STR.items()
}


class DysonBasicPurifierFanWithHumidification(DysonBasicPurifierFanWithOscillation):
    """Dyson Basic Purifier Fan with Humidification device.

    This class represents PH series devices (PH01, PH02, PH03, PH04) that combine:
    - Basic air purification (PM sensors, filters, auto mode)
    - Standard oscillation
    - Humidification capabilities
    - No advanced environmental sensors (VOC, NO2, CO2)

    Inherits from:
    - DysonBasicPurifierFanWithOscillation: Basic purification and oscillation
    """

    @property
    def oscillation_mode(self) -> HumidifyOscillationMode:
        """Return oscillation mode specific to humidification devices."""
        return HumidifyOscillationMode(self._get_field_value(self._status, "ancp"))

    @property
    def humidification(self) -> bool:
        """Return if humidification is on."""
        return self._get_field_value(self._status, "hume") == "HUMD"

    @property
    def humidification_auto_mode(self) -> bool:
        """Return if humidification auto mode is on."""
        return self._get_field_value(self._status, "haut") == "ON"

    @property
    def target_humidity(self) -> int:
        """Return target humidity in percentage."""
        return int(self._get_field_value(self._status, "humt"))

    @property
    def auto_target_humidity(self) -> int:
        """Return humidification auto mode target humidity."""
        return int(self._get_field_value(self._status, "rect"))

    @property
    def water_hardness(self) -> WaterHardness:
        """Return water hardness setting."""
        wath = self._get_field_value(self._status, "wath")
        return WATER_HARDNESS_STR_TO_ENUM.get(wath, WaterHardness.MEDIUM)

    @property
    def humidity(self) -> Optional[int]:
        """Return current humidity from environmental data."""
        if self._environmental_data is None:
            return None
        return int(self._get_field_value(self._environmental_data, "hact"))

    def enable_humidification(self) -> None:
        """Enable humidification."""
        self._set_configuration(hume="HUMD")

    def disable_humidification(self) -> None:
        """Disable humidification."""
        self._set_configuration(hume="OFF")

    def enable_humidification_auto_mode(self) -> None:
        """Enable humidification auto mode."""
        self._set_configuration(haut="ON")

    def disable_humidification_auto_mode(self) -> None:
        """Disable humidification auto mode."""
        self._set_configuration(haut="OFF")

    def set_target_humidity(self, humidity: int) -> None:
        """Set target humidity percentage."""
        self._set_configuration(humt=f"{humidity:04d}")

    def set_water_hardness(self, hardness: WaterHardness) -> None:
        """Set water hardness level."""
        payload = {"wath": WATER_HARDNESS_ENUM_TO_STR[hardness]}
        self._set_configuration(**payload)
