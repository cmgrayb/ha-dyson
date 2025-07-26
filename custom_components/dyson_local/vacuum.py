"""Vacuum platform for Dyson."""

from typing import Any, Mapping

from libdyson import (  # type: ignore[attr-defined]
    Dyson360Eye,
    Dyson360VisNav,
    VacuumEyePowerMode,
    VacuumHeuristPowerMode,
    VacuumState,
    VacuumVisNavPowerMode,
)

from homeassistant.components.vacuum import (
    ATTR_STATUS,
    StateVacuumEntity,
    VacuumEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, STATE_PAUSED
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_DEVICES, DOMAIN
from .entity import DysonEntity

SUPPORTED_FEATURES = (
    VacuumEntityFeature.START
    | VacuumEntityFeature.PAUSE
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.FAN_SPEED
    | VacuumEntityFeature.STATUS
    | VacuumEntityFeature.STATE
    | VacuumEntityFeature.BATTERY
)

DYSON_STATUS = {
    VacuumState.FAULT_CALL_HELPLINE: "Error: Call helpline",
    VacuumState.FAULT_CONTACT_HELPLINE: "Error: Contact helpline",
    VacuumState.FAULT_CRITICAL: "Error: Critical",
    VacuumState.FAULT_GETTING_INFO: "Error: Getting info",
    VacuumState.FAULT_LOST: "Error: Lost",
    VacuumState.FAULT_ON_DOCK: "Error: On dock",
    VacuumState.FAULT_ON_DOCK_CHARGED: "Error: On dock charged",
    VacuumState.FAULT_ON_DOCK_CHARGING: "Error: On dock charging",
    VacuumState.FAULT_REPLACE_ON_DOCK: "Error: Replace device on dock",
    VacuumState.FAULT_RETURN_TO_DOCK: "Error: Return to dock",
    VacuumState.FAULT_RUNNING_DIAGNOSTIC: "Error: Running diagnostic",
    VacuumState.FAULT_USER_RECOVERABLE: "Error: Blocked",
    VacuumState.FULL_CLEAN_ABANDONED: "Abandoned",
    VacuumState.FULL_CLEAN_ABORTED: "Returning home",
    VacuumState.FULL_CLEAN_CHARGING: "Charging",
    VacuumState.FULL_CLEAN_DISCOVERING: "Discovering",
    VacuumState.FULL_CLEAN_FINISHED: "Finished",
    VacuumState.FULL_CLEAN_INITIATED: "Initiated",
    VacuumState.FULL_CLEAN_NEEDS_CHARGE: "Need charging",
    VacuumState.FULL_CLEAN_PAUSED: "Paused",
    VacuumState.FULL_CLEAN_RUNNING: "Cleaning",
    VacuumState.FULL_CLEAN_TRAVERSING: "Traversing",
    VacuumState.INACTIVE_CHARGED: "Stopped - Charged",
    VacuumState.INACTIVE_CHARGING: "Stopped - Charging",
    VacuumState.INACTIVE_DISCHARGING: "Stopped - Discharging",
    VacuumState.MAPPING_ABORTED: "Mapping - Returning home",
    VacuumState.MAPPING_CHARGING: "Mapping - Charging",
    VacuumState.MAPPING_FINISHED: "Mapping - Finished",
    VacuumState.MAPPING_INITIATED: "Mapping - Initiated",
    VacuumState.MAPPING_NEEDS_CHARGE: "Mapping - Needs charging",
    VacuumState.MAPPING_PAUSED: "Mapping - Paused",
    VacuumState.MAPPING_RUNNING: "Mapping - Running",
}

DYSON_STATES = {
    VacuumState.FAULT_CALL_HELPLINE: "error",
    VacuumState.FAULT_CONTACT_HELPLINE: "error",
    VacuumState.FAULT_CRITICAL: "error",
    VacuumState.FAULT_GETTING_INFO: "error",
    VacuumState.FAULT_LOST: "error",
    VacuumState.FAULT_ON_DOCK: "error",
    VacuumState.FAULT_ON_DOCK_CHARGED: "error",
    VacuumState.FAULT_ON_DOCK_CHARGING: "error",
    VacuumState.FAULT_REPLACE_ON_DOCK: "error",
    VacuumState.FAULT_RETURN_TO_DOCK: "error",
    VacuumState.FAULT_RUNNING_DIAGNOSTIC: "error",
    VacuumState.FAULT_USER_RECOVERABLE: "error",
    VacuumState.FULL_CLEAN_ABANDONED: "returning",
    VacuumState.FULL_CLEAN_ABORTED: "returning",
    VacuumState.FULL_CLEAN_CHARGING: "docked",
    VacuumState.FULL_CLEAN_DISCOVERING: "cleaning",
    VacuumState.FULL_CLEAN_FINISHED: "docked",
    VacuumState.FULL_CLEAN_INITIATED: "cleaning",
    VacuumState.FULL_CLEAN_NEEDS_CHARGE: "returning",
    VacuumState.FULL_CLEAN_PAUSED: STATE_PAUSED,
    VacuumState.FULL_CLEAN_RUNNING: "cleaning",
    VacuumState.FULL_CLEAN_TRAVERSING: "cleaning",
    VacuumState.INACTIVE_CHARGED: "docked",
    VacuumState.INACTIVE_CHARGING: "docked",
    VacuumState.INACTIVE_DISCHARGING: "docked",
    VacuumState.MAPPING_ABORTED: "returning",
    VacuumState.MAPPING_CHARGING: STATE_PAUSED,
    VacuumState.MAPPING_FINISHED: "cleaning",
    VacuumState.MAPPING_INITIATED: "cleaning",
    VacuumState.MAPPING_NEEDS_CHARGE: "returning",
    VacuumState.MAPPING_PAUSED: STATE_PAUSED,
    VacuumState.MAPPING_RUNNING: "cleaning",
}

EYE_POWER_MODE_ENUM_TO_STR = {
    VacuumEyePowerMode.QUIET: "Quiet",
    VacuumEyePowerMode.MAX: "Max",
}
EYE_POWER_MODE_STR_TO_ENUM = {
    value: key for key, value in EYE_POWER_MODE_ENUM_TO_STR.items()
}
HEURIST_POWER_MODE_ENUM_TO_STR = {
    VacuumHeuristPowerMode.QUIET: "Quiet",
    VacuumHeuristPowerMode.HIGH: "High",
    VacuumHeuristPowerMode.MAX: "Max",
}
HEURIST_POWER_MODE_STR_TO_ENUM = {
    value: key for key, value in HEURIST_POWER_MODE_ENUM_TO_STR.items()
}
VIS_NAV_POWER_MODE_ENUM_TO_STR = {
    VacuumVisNavPowerMode.AUTO: "Auto",
    VacuumVisNavPowerMode.QUICK: "Quick",
    VacuumVisNavPowerMode.QUIET: "Quiet",
    VacuumVisNavPowerMode.BOOST: "Boost",
}
VIS_NAV_POWER_MODE_STR_TO_ENUM = {
    value: key for key, value in VIS_NAV_POWER_MODE_ENUM_TO_STR.items()
}

ATTR_POSITION = "position"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dyson vacuum from a config entry."""
    device = hass.data[DOMAIN][DATA_DEVICES][config_entry.entry_id]
    name = config_entry.data[CONF_NAME]
    entity: DysonVacuumEntity
    if isinstance(device, Dyson360Eye):
        entity = Dyson360EyeEntity(device, name)
    elif isinstance(device, Dyson360VisNav):  # Dyson360VisNav
        entity = Dyson360VisNavEntity(device, name)
    else:  # Dyson360Heurist
        entity = Dyson360HeuristEntity(device, name)
    async_add_entities([entity])


class DysonVacuumEntity(DysonEntity, StateVacuumEntity):
    """Dyson vacuum entity base class."""

    @property
    def status(self) -> str:
        """Return the status of the vacuum."""
        return DYSON_STATUS[self._device.state]  # type: ignore[attr-defined]

    @property
    def battery_level(self) -> int:
        """Return the battery level of the vacuum cleaner."""
        return self._device.battery_level  # type: ignore[attr-defined, no-any-return]

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._device.is_connected

    @property
    def supported_features(self) -> int:
        """Flag vacuum cleaner robot features that are supported."""
        return SUPPORTED_FEATURES

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Expose the status to state attributes."""
        return {
            ATTR_POSITION: str(self._device.position),  # type: ignore[attr-defined]
            ATTR_STATUS: self.status,
        }

    def pause(self) -> None:
        """Pause the device."""
        self._device.pause()  # type: ignore[attr-defined]

    def return_to_base(self, **kwargs: Any) -> None:
        """Return the device to base."""
        self._device.abort()  # type: ignore[attr-defined]


class Dyson360EyeEntity(DysonVacuumEntity):
    """Dyson 360 Eye robot vacuum entity."""

    @property
    def fan_speed(self) -> str:
        """Return the fan speed of the vacuum cleaner."""
        return EYE_POWER_MODE_ENUM_TO_STR[self._device.power_mode]  # type: ignore[attr-defined]

    @property
    def fan_speed_list(self) -> list[str]:
        """Get the list of available fan speed steps of the vacuum cleaner."""
        return list(EYE_POWER_MODE_STR_TO_ENUM.keys())

    def start(self) -> None:
        """Start the device."""
        if self.state == STATE_PAUSED:
            self._device.resume()  # type: ignore[attr-defined]
        else:
            self._device.start()  # type: ignore[attr-defined]

    def set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        """Set fan speed."""
        self._device.set_power_mode(EYE_POWER_MODE_STR_TO_ENUM[fan_speed])  # type: ignore[attr-defined]


class Dyson360HeuristEntity(DysonVacuumEntity):
    """Dyson 360 Heurist robot vacuum entity."""

    @property
    def fan_speed(self) -> str:
        """Return the fan speed of the vacuum cleaner."""
        return HEURIST_POWER_MODE_ENUM_TO_STR[self._device.current_power_mode]  # type: ignore[attr-defined]

    @property
    def fan_speed_list(self) -> list[str]:
        """Get the list of available fan speed steps of the vacuum cleaner."""
        return list(HEURIST_POWER_MODE_STR_TO_ENUM.keys())

    def start(self) -> None:
        """Start the device."""
        if self.state == STATE_PAUSED:
            self._device.resume()  # type: ignore[attr-defined]
        else:
            self._device.start_all_zones()  # type: ignore[attr-defined]

    def set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        """Set fan speed."""
        self._device.set_default_power_mode(HEURIST_POWER_MODE_STR_TO_ENUM[fan_speed])  # type: ignore[attr-defined]


class Dyson360VisNavEntity(Dyson360HeuristEntity):
    """Dyson 360 Vis Nav robot vacuum entity."""

    @property
    def fan_speed(self) -> str:
        """Return the fan speed of the vacuum cleaner."""
        return VIS_NAV_POWER_MODE_ENUM_TO_STR[self._device.current_power_mode]  # type: ignore[attr-defined]

    @property
    def fan_speed_list(self) -> list[str]:
        """Get the list of available fan speed steps of the vacuum cleaner."""
        return list(VIS_NAV_POWER_MODE_STR_TO_ENUM.keys())

    def set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        """Set fan speed."""
        self._device.set_default_power_mode(VIS_NAV_POWER_MODE_STR_TO_ENUM[fan_speed])  # type: ignore[attr-defined]
