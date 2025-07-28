"""Dyson Advanced Purifier Fan with full environmental monitoring."""

from typing import Optional

from .dyson_basic_purifier_fan import DysonBasicPurifierFanWithOscillation


class DysonAdvancedPurifierFan(DysonBasicPurifierFanWithOscillation):
    """Dyson Advanced Purifier Fan - includes VOC, NO2, CO2, and other advanced environmental sensors."""

    @property
    def volatile_organic_compounds(self) -> float:
        """Return the index value for VOC"""
        return self._get_environmental_field_value("va10", divisor=10)

    @property
    def nitrogen_dioxide(self) -> float:
        """Return the index value for nitrogen."""
        return self._get_environmental_field_value("noxl", divisor=10)

    @property
    def carbon_dioxide(self) -> Optional[int]:
        """Return the PPM of carbon dioxide"""
        return self._get_environmental_field_value("co2r")

    @property
    def humidity(self) -> Optional[int]:
        """Return humidity in percentage."""
        return self._get_environmental_field_value("hact")

    @property
    def temperature(self) -> Optional[float]:
        """Return temperature in Kelvin."""
        temp_kelvin = self._get_environmental_field_value("tact")
        if temp_kelvin is not None:
            return float(temp_kelvin) / 10  # Convert from tenths of Kelvin
        return None

    @property
    def tilt(self) -> int:
        """Return the tilt in degrees."""
        return int(
            self._get_field_value(self._status, "otau")
            or self._get_field_value(self._status, "otal")
        )
