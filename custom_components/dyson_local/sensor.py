"""Sensor platform for dyson."""

from typing import Callable, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_MILLIGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_MILLION,
    CONF_NAME,
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DATA_COORDINATORS, DATA_DEVICES, DOMAIN
from .entity import DysonEntity
from .vendor.libdyson import (
    Dyson360Eye,
    Dyson360Heurist,
    Dyson360VisNav,
    DysonBigQuiet,
    DysonDevice,
    DysonPureCoolLink,
    DysonPurifierHumidifyCool,
)
from .vendor.libdyson.const import MessageType
from .vendor.libdyson.dyson_basic_purifier_fan import DysonBasicPurifierFan


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Callable
) -> None:
    """Set up Dyson sensor from a config entry."""
    device = hass.data[DOMAIN][DATA_DEVICES][config_entry.entry_id]
    name = config_entry.data[CONF_NAME]
    if (
        isinstance(device, Dyson360Eye)
        or isinstance(device, Dyson360Heurist)
        or isinstance(device, Dyson360VisNav)
    ):
        entities = [DysonBatterySensor(device, name)]
    else:
        coordinator = hass.data[DOMAIN][DATA_COORDINATORS][config_entry.entry_id]
        entities = []

        # Add environmental sensors based on device capabilities
        if hasattr(device, "humidity"):
            entities.append(DysonHumiditySensor(coordinator, device, name))
        if hasattr(device, "temperature"):
            entities.append(DysonTemperatureSensor(coordinator, device, name))
        if hasattr(device, "volatile_organic_compounds"):
            entities.append(DysonVOCSensor(coordinator, device, name))

        if isinstance(device, DysonPureCoolLink):
            entities.extend(
                [
                    DysonFilterLifeSensor(device, name),
                    DysonFilterLifeSensorPercentage(device, name),
                    DysonParticulatesSensor(coordinator, device, name),
                ]
            )
        else:
            if isinstance(device, DysonBigQuiet):
                if (
                    hasattr(device, "carbon_dioxide")
                    and device.carbon_dioxide is not None
                ):
                    entities.append(DysonCarbonDioxideSensor(coordinator, device, name))

            # Add particulate matter sensors based on device capabilities
            # Always create PM sensors for basic purifiers (they have them even if not detected during discovery)
            if isinstance(device, DysonBasicPurifierFan) or hasattr(
                device, "particulate_matter_2_5"
            ):
                entities.append(DysonPM25Sensor(coordinator, device, name))
            if isinstance(device, DysonBasicPurifierFan) or hasattr(
                device, "particulate_matter_10"
            ):
                entities.append(DysonPM10Sensor(coordinator, device, name))
            if hasattr(device, "nitrogen_dioxide"):
                entities.append(DysonNO2Sensor(coordinator, device, name))
            if device.carbon_filter_life is None:
                entities.append(DysonCombinedFilterLifeSensor(device, name))
            else:
                entities.extend(
                    [
                        DysonCarbonFilterLifeSensor(device, name),
                        DysonHEPAFilterLifeSensor(device, name),
                    ]
                )
        if isinstance(device, DysonPurifierHumidifyCool):
            entities.append(DysonNextDeepCleanSensor(device, name))
        if hasattr(device, "formaldehyde") and device.formaldehyde is not None:
            entities.append(DysonHCHOSensor(coordinator, device, name))
    async_add_entities(entities)


class DysonSensor(SensorEntity, DysonEntity):  # type: ignore[misc]
    """Base class for a Dyson sensor."""

    _MESSAGE_TYPE = MessageType.STATE
    _SENSOR_TYPE: Optional[str] = None
    _SENSOR_NAME: Optional[str] = None

    def __init__(self, device: DysonDevice, name: str):
        """Initialize the sensor."""
        super().__init__(device, name)

    @property
    def sub_name(self):
        """Return the name of the Dyson sensor."""
        return self._SENSOR_NAME

    @property
    def sub_unique_id(self):
        """Return the sensor's unique id."""
        return self._SENSOR_TYPE


class DysonSensorEnvironmental(CoordinatorEntity, DysonSensor):  # type: ignore[misc]
    """Dyson environmental sensor."""

    _MESSAGE_TYPE = MessageType.ENVIRONMENTAL

    def __init__(
        self, coordinator: DataUpdateCoordinator, device: DysonDevice, name: str
    ) -> None:
        """Initialize the environmental sensor."""
        CoordinatorEntity.__init__(self, coordinator)
        DysonSensor.__init__(self, device, name)

    @property
    def available(self) -> bool:
        """Return if the sensor is available."""
        # For basic purifiers, environmental sensors should be available
        # even if no data has been received yet
        from .vendor.libdyson.dyson_basic_purifier_fan import DysonBasicPurifierFan

        if isinstance(self._device, DysonBasicPurifierFan):
            return True

        # For other devices, use the default coordinator availability
        return super().available if hasattr(super(), "available") else True


class DysonBatterySensor(DysonSensor):
    """Dyson battery sensor."""

    _SENSOR_TYPE = "battery_level"
    _SENSOR_NAME = "Battery Level"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> int:  # type: ignore[override]
        """Return the state of the sensor."""
        return self._device.battery_level  # type: ignore[attr-defined]


class DysonFilterLifeSensor(DysonSensor):
    """Dyson filter life sensor (in hours) for Pure Cool Link."""

    _SENSOR_TYPE = "filter_life"
    _SENSOR_NAME = "Filter Life"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:filter-outline"
    _attr_native_unit_of_measurement = UnitOfTime.HOURS

    @property
    def native_value(self) -> int:  # type: ignore[override]
        """Return the state of the sensor."""
        return self._device.filter_life  # type: ignore[attr-defined]


class DysonFilterLifeSensorPercentage(DysonSensor):
    """Dyson filter life sensor (in percentage) for Pure Cool Link."""

    _SENSOR_TYPE = "filter_life_percentage"
    _SENSOR_NAME = "Filter Life Percentage"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:filter-outline"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_suggested_display_precision = 0

    @property
    def native_value(self) -> float:
        """Return the state of the sensor calculated to a %."""
        return (self._device.filter_life / 4300) * 100


class DysonCarbonFilterLifeSensor(DysonSensor):
    """Dyson carbon filter life sensor (in percentage) for Pure Cool."""

    _SENSOR_TYPE = "carbon_filter_life"
    _SENSOR_NAME = "Carbon Filter Life"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:filter-outline"
    _attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> int:  # type: ignore[override]
        """Return the state of the sensor."""
        return self._device.carbon_filter_life  # type: ignore[attr-defined]


class DysonHEPAFilterLifeSensor(DysonSensor):
    """Dyson HEPA filter life sensor (in percentage) for Pure Cool."""

    _SENSOR_TYPE = "hepa_filter_life"
    _SENSOR_NAME = "HEPA Filter Life"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:filter-outline"
    _attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> int:  # type: ignore[override]
        """Return the state of the sensor."""
        return self._device.hepa_filter_life  # type: ignore[attr-defined]


class DysonCombinedFilterLifeSensor(DysonSensor):
    """Dyson combined filter life sensor (in percentage) for Pure Cool."""

    _SENSOR_TYPE = "combined_filter_life"
    _SENSOR_NAME = "Filter Life"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:filter-outline"
    _attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> int:  # type: ignore[override]
        """Return the state of the sensor."""
        return self._device.hepa_filter_life  # type: ignore[attr-defined]


class DysonNextDeepCleanSensor(DysonSensor):
    """Sensor of time until next deep clean (in hours) for Dyson Pure Humidify+Cool."""

    _SENSOR_TYPE = "next_deep_clean"
    _SENSOR_NAME = "Next Deep Clean"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:filter-outline"
    _attr_native_unit_of_measurement = UnitOfTime.HOURS

    @property
    def native_value(self) -> Optional[int]:  # type: ignore[override]
        """Return the state of the sensor."""
        if (value := self._device.time_until_next_clean) >= 0:  # type: ignore[attr-defined]
            return value
        return None

    @property
    def available(self) -> bool:  # type: ignore[override]
        """Return available only if device not in off, init or failed states."""
        return isinstance(self._device.time_until_next_clean, (int, float))  # type: ignore[attr-defined]


class DysonHumiditySensor(DysonSensorEnvironmental):
    """Dyson humidity sensor."""

    _SENSOR_TYPE = "humidity"
    _SENSOR_NAME = "Humidity"
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Optional[int]:  # type: ignore[override]
        """Return the state of the sensor."""
        if (value := self._device.humidity) >= 0:  # type: ignore[attr-defined]
            return value
        return None

    @property
    def available(self) -> bool:
        """Return available only if device not in off, init or failed states."""
        return isinstance(self._device.humidity, (int, float))  # type: ignore[attr-defined]


class DysonTemperatureSensor(DysonSensorEnvironmental):
    """Dyson temperature sensor."""

    _SENSOR_TYPE = "temperature"
    _SENSOR_NAME = "Temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Optional[float]:  # type: ignore[override]
        """Return the "native" value for this sensor.
        Note that as of 2021-10-28, Home Assistant does not support converting
        from Kelvin native unit to Celsius/Fahrenheit. So we return the Celsius
        value as it's the easiest to calculate.
        """
        if (value := self._device.temperature) >= 0:  # type: ignore[attr-defined]
            return value - 273.15
        return None

    @property
    def available(self) -> bool:
        """Return available only if device not in off, init or failed states."""
        return isinstance(self._device.temperature, (int, float))  # type: ignore[attr-defined]


class DysonPM25Sensor(DysonSensorEnvironmental):
    """Dyson sensor for PM 2.5 fine particulate matters."""

    _SENSOR_TYPE = "pm25"
    _SENSOR_NAME = "PM 2.5"
    _attr_device_class = SensorDeviceClass.PM25
    _attr_native_unit_of_measurement = CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Optional[int]:  # type: ignore[override]
        """Return the state of the sensor."""
        try:
            if (value := self._device.particulate_matter_2_5) is not None and value >= 0:  # type: ignore[attr-defined]
                return int(value)
        except (AttributeError, TypeError, ValueError):
            pass
        return None

    @property
    def available(self) -> bool:
        """Return available only if device not in off, init or failed states."""
        try:
            # For basic purifiers, PM sensors should always be available
            from .vendor.libdyson.dyson_basic_purifier_fan import DysonBasicPurifierFan

            if isinstance(self._device, DysonBasicPurifierFan):
                return True

            value = self._device.particulate_matter_2_5  # type: ignore[attr-defined]
            return value is not None and isinstance(value, (int, float))
        except (AttributeError, TypeError):
            return False


class DysonPM10Sensor(DysonSensorEnvironmental):
    """Dyson sensor for PM 10 particulate matters."""

    _SENSOR_TYPE = "pm10"
    _SENSOR_NAME = "PM 10"
    _attr_device_class = SensorDeviceClass.PM10
    _attr_native_unit_of_measurement = CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Optional[int]:  # type: ignore[override]
        """Return the state of the sensor."""
        try:
            if (value := self._device.particulate_matter_10) is not None and value >= 0:  # type: ignore[attr-defined]
                return int(value)
        except (AttributeError, TypeError, ValueError):
            pass
        return None

    @property
    def available(self) -> bool:
        """Return available only if device not in off, init or failed states."""
        try:
            # For basic purifiers, PM sensors should always be available
            from .vendor.libdyson.dyson_basic_purifier_fan import DysonBasicPurifierFan

            if isinstance(self._device, DysonBasicPurifierFan):
                return True

            value = self._device.particulate_matter_10  # type: ignore[attr-defined]
            return value is not None and isinstance(value, (int, float))
        except (AttributeError, TypeError):
            return False


class DysonParticulatesSensor(DysonSensorEnvironmental):
    """Dyson sensor for particulate matters for "Link" devices."""

    _SENSOR_TYPE = "aqi"
    _SENSOR_NAME = "Air Quality Index"
    _attr_device_class = SensorDeviceClass.AQI
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Optional[int]:  # type: ignore[override]
        """Return the state of the sensor."""
        if (value := self._device.particulates) >= 0:  # type: ignore[attr-defined]
            return value
        return None

    @property
    def available(self) -> bool:
        """Return available only if device not in off, init or failed states."""
        return isinstance(self._device.particulates, (int, float))  # type: ignore[attr-defined]


class DysonVOCSensor(DysonSensorEnvironmental):
    """Dyson sensor for volatile organic compounds."""

    _SENSOR_TYPE = "voc-index"
    _SENSOR_NAME = "Volatile Organic Compounds Index"
    _attr_device_class = SensorDeviceClass.AQI
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Optional[int]:  # type: ignore[override]
        """Return the state of the sensor."""
        if (value := self._device.volatile_organic_compounds) >= 0:  # type: ignore[attr-defined]
            return value
        return None

    @property
    def available(self) -> bool:
        """Return available only if device not in off, init or failed states."""
        return isinstance(self._device.volatile_organic_compounds, (int, float))  # type: ignore[attr-defined]


class DysonNO2Sensor(DysonSensorEnvironmental):
    """Dyson sensor for Nitrogen Dioxide."""

    _SENSOR_TYPE = "no2-index"
    _SENSOR_NAME = "Nitrogen Dioxide Index"
    _attr_device_class = SensorDeviceClass.AQI
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Optional[int]:  # type: ignore[override]
        """Return the state of the sensor."""
        if (value := self._device.nitrogen_dioxide) >= 0:  # type: ignore[attr-defined]
            return value
        return None

    @property
    def available(self) -> bool:
        """Return available only if device not in off, init or failed states."""
        return isinstance(self._device.nitrogen_dioxide, (int, float))  # type: ignore[attr-defined]


class DysonHCHOSensor(DysonSensorEnvironmental):
    """Dyson sensor for Formaldehyde."""

    _SENSOR_TYPE = "hcho-mg"
    _SENSOR_NAME = "HCHO"

    _attr_native_unit_of_measurement = CONCENTRATION_MILLIGRAMS_PER_CUBIC_METER
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Optional[float]:  # type: ignore[override]
        """Return the state of the sensor."""
        if (value := self._device.formaldehyde) >= 0:  # type: ignore[attr-defined]
            return value
        return None

    @property
    def available(self) -> bool:
        """Return available only if device not in off, init or failed states."""
        return isinstance(self._device.formaldehyde, (int, float))  # type: ignore[attr-defined]


class DysonCarbonDioxideSensor(DysonSensorEnvironmental):
    """Dyson sensor for Carbon Dioxide."""

    _SENSOR_TYPE = "c02"
    _SENSOR_NAME = "Carbon Dioxide"

    _attr_device_class = SensorDeviceClass.CO2
    _attr_native_unit_of_measurement = CONCENTRATION_PARTS_PER_MILLION
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Optional[float]:  # type: ignore[override]
        """Return the state of the sensor."""
        if (value := self._device.carbon_dioxide) >= 0:  # type: ignore[attr-defined]
            return value
        return None

    @property
    def available(self) -> bool:
        """Return available only if device not in off, init or failed states."""
        return isinstance(self._device.carbon_dioxide, (int, float))  # type: ignore[attr-defined]  # type: ignore[attr-defined]
