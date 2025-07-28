"""Dyson Basic Purifier Fan with Heating capability."""

from typing import Optional

from .dyson_basic_purifier_fan import DysonBasicPurifierFanWithOscillation
from .dyson_device import DysonHeatingDevice


class DysonBasicPurifierFanWithHeating(
    DysonBasicPurifierFanWithOscillation, DysonHeatingDevice
):
    """Dyson Basic Purifier Fan with Heating - combines basic purification with heating functionality.

    This class is for devices like HP04, HP07, HP09 series that have:
    - Basic purification (PM sensors, filters, auto mode)
    - Heating capability (hmod, hmax)
    - Basic oscillation
    - NO advanced environmental sensors (VOC, NO2, CO2)

    For devices with advanced sensors + heating, use AdvancedPurifierFanWithHeating instead.
    """

    @property
    def temperature_celsius(self) -> Optional[float]:
        """Return temperature in Celsius."""
        temp_kelvin = self.temperature
        if temp_kelvin is not None:
            return temp_kelvin - 273.15
        return None

    @property
    def temperature_fahrenheit(self) -> Optional[float]:
        """Return temperature in Fahrenheit."""
        temp_celsius = self.temperature_celsius
        if temp_celsius is not None:
            return (temp_celsius * 9 / 5) + 32
        return None
