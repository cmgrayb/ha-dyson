"""Dyson Advanced Oscillation Fan device."""

import logging
from typing import Optional

from .dyson_basic_fan import DysonBasicFan

_LOGGER = logging.getLogger(__name__)


class DysonAdvancedOscillationFan(DysonBasicFan):
    """Dyson fan with advanced angle-controlled oscillation.

    This class extends DysonBasicFan with:
    - Oscillation with angle control (osal/osau)
    - Angle validation and setting
    - Sleep timer functionality

    This is suitable for devices like AM12 that have oscillation
    controls but no air purification features.
    """

    @property
    def oscillation_status(self) -> bool:
        """Return the status of oscillation."""
        return self._get_field_value(self._status, "oscs") == "ON"

    @property
    def oscillation_angle_low(self) -> int:
        """Return oscillation low angle."""
        osal = self._get_field_value(self._status, "osal")
        return int(osal) if osal is not None else 0

    @property
    def oscillation_angle_high(self) -> int:
        """Return oscillation high angle."""
        osau = self._get_field_value(self._status, "osau")
        return int(osau) if osau is not None else 0

    @property
    def sleep_timer(self) -> Optional[int]:
        """Return sleep timer in minutes."""
        sltm = self._get_field_value(self._status, "sltm")
        if sltm == "OFF" or sltm is None:
            return None
        try:
            return int(sltm)
        except (ValueError, TypeError):
            return None

    def enable_oscillation(
        self,
        angle_low: Optional[int] = None,
        angle_high: Optional[int] = None,
    ) -> None:
        """Turn on oscillation with optional angle control."""
        _LOGGER.info(
            "enable_oscillation() called for device %s with angles %s, %s",
            self.serial,
            angle_low,
            angle_high,
        )

        # Use current angles if not provided
        if angle_low is None:
            angle_low = self.oscillation_angle_low or 5
        if angle_high is None:
            angle_high = self.oscillation_angle_high or 355

        # Validate angles
        if not 5 <= angle_low <= 355:
            raise ValueError("angle_low must be between 5 and 355")
        if not 5 <= angle_high <= 355:
            raise ValueError("angle_high must be between 5 and 355")
        if angle_low != angle_high and angle_low + 30 > angle_high:
            raise ValueError(
                "angle_high must be either equal to angle_low or at least 30 larger than angle_low"
            )

        # Determine oscillation format (some devices use OION/OIOF, others ON/OFF)
        current_oscillation_raw = self._get_field_value(self._status, "oson")
        if current_oscillation_raw in ["OION", "OIOF"]:
            oson = "OION"
        else:
            oson = "ON"

        _LOGGER.info(
            "Setting oscillation config for device %s: oson=%s, angle_low=%s, angle_high=%s",
            self.serial,
            oson,
            angle_low,
            angle_high,
        )

        self._set_configuration(
            oson=oson,
            fpwr="ON",
            ancp="CUST",
            osal=f"{angle_low:04d}",
            osau=f"{angle_high:04d}",
        )

    def disable_oscillation(self) -> None:
        """Turn off oscillation."""
        _LOGGER.info("disable_oscillation() called for device %s", self.serial)

        # Use the appropriate off command based on current state
        current_oscillation_raw = self._get_field_value(self._status, "oson")
        if current_oscillation_raw in ["OION", "OIOF"]:
            oson = "OIOF"
        else:
            oson = "OFF"

        _LOGGER.info("Setting oson=%s for device %s", oson, self.serial)
        self._set_configuration(oson=oson)

    def set_sleep_timer(self, duration: int) -> None:
        """Set sleep timer in minutes."""
        if not 1 <= duration <= 540:
            raise ValueError("Duration must be between 1 and 540 minutes")

        _LOGGER.debug("set_sleep_timer(%d) called for device %s", duration, self.serial)
        self._set_configuration(sltm=f"{duration:04d}")

    def disable_sleep_timer(self) -> None:
        """Disable sleep timer."""
        _LOGGER.debug("disable_sleep_timer() called for device %s", self.serial)
        self._set_configuration(sltm="OFF")
