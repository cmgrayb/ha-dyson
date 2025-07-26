"""Humidifier platform for Dyson."""

from typing import Callable, Optional

from homeassistant.components.humidifier import (
    HumidifierDeviceClass,
    HumidifierEntity,
    HumidifierEntityFeature,
)
from homeassistant.components.humidifier.const import MODE_AUTO, MODE_NORMAL
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant

from .const import DATA_DEVICES, DOMAIN
from .entity import DysonEntity
from .vendor.libdyson import MessageType

AVAILABLE_MODES = [MODE_NORMAL, MODE_AUTO]

SUPPORTED_FEATURES = HumidifierEntityFeature.MODES


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Callable
) -> None:
    """Set up Dyson humidifier from a config entry."""
    device = hass.data[DOMAIN][DATA_DEVICES][config_entry.entry_id]
    name = config_entry.data[CONF_NAME]
    async_add_entities([DysonHumidifierEntity(device, name)])


class DysonHumidifierEntity(DysonEntity, HumidifierEntity):  # type: ignore[misc]
    """Dyson humidifier entity."""

    _MESSAGE_TYPE = MessageType.STATE

    _attr_device_class = HumidifierDeviceClass.HUMIDIFIER
    _attr_available_modes = AVAILABLE_MODES
    _attr_max_humidity = 70
    _attr_min_humidity = 30
    _attr_supported_features = HumidifierEntityFeature.MODES

    @property
    def is_on(self) -> bool:  # type: ignore[override]
        """Return if humidification is on."""
        return self._device.humidification  # type: ignore[attr-defined]

    @property
    def target_humidity(self) -> Optional[int]:  # type: ignore[override]
        """Return the target."""
        if self._device.humidification_auto_mode:  # type: ignore[attr-defined]
            return None

        return self._device.target_humidity  # type: ignore[attr-defined]

    @property
    def mode(self) -> str:  # type: ignore[override]
        """Return current mode."""
        return MODE_AUTO if self._device.humidification_auto_mode else MODE_NORMAL  # type: ignore[attr-defined]

    def turn_on(self, **kwargs) -> None:
        """Turn on humidification."""
        self._device.enable_humidification()  # type: ignore[attr-defined]

    def turn_off(self, **kwargs) -> None:
        """Turn off humidification."""
        self._device.disable_humidification()  # type: ignore[attr-defined]

    def set_humidity(self, humidity: int) -> None:
        """Set target humidity."""
        self._device.set_target_humidity(humidity)  # type: ignore[attr-defined]
        self.set_mode(MODE_NORMAL)

    def set_mode(self, mode: str) -> None:
        """Set humidification mode."""
        if mode == MODE_AUTO:
            self._device.enable_humidification_auto_mode()  # type: ignore[attr-defined]
        elif mode == MODE_NORMAL:
            self._device.disable_humidification_auto_mode()  # type: ignore[attr-defined]
        else:
            raise ValueError(f"Invalid mode: {mode}")
