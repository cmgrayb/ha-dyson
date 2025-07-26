"""Dyson climate platform."""

import logging
from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    FAN_DIFFUSE,
    FAN_FOCUS,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, CONF_NAME, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_DEVICES, DOMAIN
from .entity import DysonEntity
from .utils import environmental_property
from .vendor.libdyson import DysonPureHotCoolLink  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

HVAC_MODES = [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT]
FAN_MODES = [FAN_FOCUS, FAN_DIFFUSE]
SUPPORT_FLAGS = (
    ClimateEntityFeature.TARGET_TEMPERATURE
    | ClimateEntityFeature.TURN_ON
    | ClimateEntityFeature.TURN_OFF
)
SUPPORT_FLAGS_LINK = SUPPORT_FLAGS | ClimateEntityFeature.FAN_MODE


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dyson climate from a config entry."""
    device = hass.data[DOMAIN][DATA_DEVICES][config_entry.entry_id]
    name = config_entry.data[CONF_NAME]
    entity: DysonClimateEntity
    if isinstance(device, DysonPureHotCoolLink):
        entity = DysonPureHotCoolLinkEntity(device, name)
    else:  # DysonPureHotCool
        entity = DysonPureHotCoolEntity(device, name)
    async_add_entities([entity])


class DysonClimateEntity(ClimateEntity, DysonEntity):
    """Dyson climate entity base class."""

    def __init__(self, device: Any, name: str) -> None:
        """Initialize the climate entity."""
        super().__init__(device, name)

        # Set attributes to avoid property override issues
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT]
        self._attr_supported_features = SUPPORT_FLAGS
        self._attr_min_temp = 1
        self._attr_max_temp = 37

    _enable_turn_on_off_backwards_compatibility = False

    @property
    def hvac_mode(self) -> HVACMode:
        """Return hvac operation."""
        if not self._device.is_on:  # type: ignore[attr-defined]
            return HVACMode.OFF
        if self._device.heat_mode_is_on:  # type: ignore[attr-defined]
            return HVACMode.HEAT
        return HVACMode.COOL

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current running hvac operation."""
        if not self._device.is_on:  # type: ignore[attr-defined]
            return HVACAction.OFF
        if self._device.heat_mode_is_on:  # type: ignore[attr-defined]
            if self._device.heat_status_is_on:  # type: ignore[attr-defined]
                return HVACAction.HEATING
            return HVACAction.IDLE
        return HVACAction.COOLING

    def turn_on(self) -> None:
        """Turn on the device."""
        self._device.turn_on()  # type: ignore[attr-defined]

    def turn_off(self) -> None:
        """Turn off the device."""
        self._device.turn_off()  # type: ignore[attr-defined]

    @property
    def target_temperature(self) -> float:
        """Return the target temperature."""
        return self._device.heat_target - 273  # type: ignore[attr-defined, no-any-return]

    @environmental_property
    def _current_temperature_kelvin(self) -> int:
        """Return the current temperature in kelvin."""
        return self._device.temperature  # type: ignore[attr-defined, no-any-return]

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        temperature_kelvin = self._current_temperature_kelvin
        if isinstance(temperature_kelvin, str):
            return None
        return float(f"{(temperature_kelvin - 273.15):.1f}")

    @environmental_property
    def current_humidity(self) -> int:
        """Return the current humidity."""
        return self._device.humidity  # type: ignore[attr-defined, no-any-return]

    def set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        target_temp = kwargs.get(ATTR_TEMPERATURE)
        # Check if a temperature was sent
        if target_temp is None:
            _LOGGER.error("Missing target temperature %s", kwargs)
            return
        # Limit the target temperature into acceptable range
        if target_temp < self.min_temp or target_temp > self.max_temp:
            _LOGGER.warning("Temperature requested is outside min/max range, adjusting")
            target_temp = min(self.max_temp, target_temp)
            target_temp = max(self.min_temp, target_temp)
        _LOGGER.debug("Set %s temperature %s", self.name, target_temp)
        self._device.set_heat_target(target_temp + 273)  # type: ignore[attr-defined]

    def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new hvac mode."""
        _LOGGER.debug("Set %s heat mode %s", self.name, hvac_mode)
        if hvac_mode == HVACMode.OFF:
            self._device.turn_off()  # type: ignore[attr-defined]
        elif not self._device.is_on:  # type: ignore[attr-defined]
            self._device.turn_on()  # type: ignore[attr-defined]
        if hvac_mode == HVACMode.HEAT:
            self._device.enable_heat_mode()  # type: ignore[attr-defined]
        elif hvac_mode == HVACMode.COOL:
            self._device.disable_heat_mode()  # type: ignore[attr-defined]


class DysonPureHotCoolLinkEntity(DysonClimateEntity):
    """Dyson Pure Hot+Cool Link entity."""

    def __init__(self, device: Any, name: str) -> None:
        """Initialize the Pure Hot+Cool Link entity."""
        super().__init__(device, name)
        # Add fan mode support for Link devices
        self._attr_supported_features = SUPPORT_FLAGS_LINK
        self._attr_fan_modes = FAN_MODES

    @property
    def fan_mode(self) -> str:
        """Return the fan setting."""
        if self._device.focus_mode:  # type: ignore[attr-defined]
            return FAN_FOCUS
        return FAN_DIFFUSE

    def set_fan_mode(self, fan_mode: str) -> None:
        """Set fan mode of the device."""
        _LOGGER.debug("Set %s focus mode %s", self.name, fan_mode)
        if fan_mode == FAN_FOCUS:
            self._device.enable_focus_mode()  # type: ignore[attr-defined]
        elif fan_mode == FAN_DIFFUSE:
            self._device.disable_focus_mode()  # type: ignore[attr-defined]


class DysonPureHotCoolEntity(DysonClimateEntity):
    """Dyson Pure Hot+Cool entity."""
