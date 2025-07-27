"""Binary sensor platform for dyson."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory  # type: ignore[attr-defined]
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_DEVICES, DOMAIN
from .entity import DysonEntity
from .vendor.libdyson import (
    Dyson360Eye,
    Dyson360Heurist,
    Dyson360VisNav,
    DysonPureHotCoolLink,
)

ICON_BIN_FULL = "mdi:delete-variant"


class DysonBinarySensor(BinarySensorEntity, DysonEntity):
    """Base class for Dyson binary sensors."""

    def __init__(self, device: Any, name: str) -> None:
        """Initialize the binary sensor."""
        super().__init__(device, name)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dyson binary sensor from a config entry."""
    device = hass.data[DOMAIN][DATA_DEVICES][config_entry.entry_id]
    name = config_entry.data[CONF_NAME]
    entities: list[BinarySensorEntity] = []
    if isinstance(device, Dyson360Eye):
        entities.append(DysonVacuumBatteryChargingSensor(device, name))
    if isinstance(device, Dyson360Heurist):
        entities.extend(
            [
                DysonVacuumBatteryChargingSensor(device, name),
                Dyson360HeuristBinFullSensor(device, name),
            ]
        )
    if isinstance(device, Dyson360VisNav):
        entities.extend(
            [
                DysonVacuumBatteryChargingSensor(device, name),
                Dyson360VisNavBinFullSensor(device, name),
            ]
        )
    if isinstance(device, DysonPureHotCoolLink):
        entities.extend([DysonPureHotCoolLinkTiltSensor(device, name)])
    async_add_entities(entities)


class DysonVacuumBatteryChargingSensor(DysonBinarySensor):
    """Dyson vacuum battery charging sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    def __init__(self, device: Any, name: str) -> None:
        """Initialize the sensor."""
        super().__init__(device, name)
        self._attr_is_on = getattr(self._device, "is_charging", False)

    @property
    def sub_name(self) -> str:
        """Return the name of the sensor."""
        return "Battery Charging"

    @property
    def sub_unique_id(self) -> str:
        """Return the sensor's unique id."""
        return "battery_charging"


class Dyson360HeuristBinFullSensor(DysonBinarySensor):
    """Dyson 360 Heurist bin full sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = ICON_BIN_FULL

    def __init__(self, device: Any, name: str) -> None:
        """Initialize the sensor."""
        super().__init__(device, name)
        self._attr_is_on = getattr(device, "is_bin_full", False)

    @property
    def sub_name(self) -> str:
        """Return the name of the sensor."""
        return "Bin Full"

    @property
    def sub_unique_id(self) -> str:
        """Return the sensor's unique id."""
        return "bin_full"


class Dyson360VisNavBinFullSensor(DysonBinarySensor):
    """Dyson 360 VisNav bin full sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = ICON_BIN_FULL

    def __init__(self, device: Any, name: str) -> None:
        """Initialize the sensor."""
        super().__init__(device, name)
        self._attr_is_on = getattr(device, "is_bin_full", False)

    @property
    def sub_name(self) -> str:
        """Return the name of the sensor."""
        return "Bin Full"

    @property
    def sub_unique_id(self) -> str:
        """Return the sensor's unique id."""
        return "bin_full"


class DysonPureHotCoolLinkTiltSensor(DysonBinarySensor):
    """Dyson Pure Hot+Cool Link tilt sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:angle-acute"

    def __init__(self, device: Any, name: str) -> None:
        """Initialize the sensor."""
        super().__init__(device, name)
        self._attr_is_on = getattr(device, "tilt", False)

    @property
    def sub_name(self) -> str:
        """Return the name of the sensor."""
        return "Tilt"

    @property
    def sub_unique_id(self) -> str:
        """Return the sensor's unique id."""
        return "tilt"
