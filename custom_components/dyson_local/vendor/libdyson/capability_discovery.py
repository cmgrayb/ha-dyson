"""Dynamic Device Capability Discovery System for Dyson devices."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import logging
from typing import Any, Dict, List, Optional, Set, Type, Union

_LOGGER = logging.getLogger(__name__)


class DeviceCapability(Enum):
    """Enumeration of device capabilities that can be dynamically discovered."""

    # Basic Fan Capabilities
    BASIC_FAN_CONTROL = "basic_fan_control"  # fpwr, fnsp, fnst
    BASIC_OSCILLATION = "basic_oscillation"  # oson
    NIGHT_MODE = "night_mode"  # nmod, nmdv
    SLEEP_TIMER = "sleep_timer"  # sltm

    # Advanced Fan Capabilities
    ANGLE_OSCILLATION = "angle_oscillation"  # osal, osau, ancp
    FRONT_AIRFLOW = "front_airflow"  # fdir

    # Air Purification Capabilities
    AUTO_MODE = "auto_mode"  # auto
    FILTER_MONITORING = "filter_monitoring"  # cflr, hflr
    PM_SENSORS = "pm_sensors"  # p25r, p10r, pm25, pm10

    # Advanced Environmental Monitoring
    VOC_SENSOR = "voc_sensor"  # va10
    NO2_SENSOR = "no2_sensor"  # noxl
    CO2_SENSOR = "co2_sensor"  # co2r
    HUMIDITY_SENSOR = "humidity_sensor"  # hact
    TEMPERATURE_SENSOR = "temperature_sensor"  # tact

    # Humidification
    HUMIDIFICATION = "humidification"  # hume, haut, humt
    WATER_HARDNESS = "water_hardness"  # wath

    # Heating
    HEATING = "heating"  # hmod, hmax

    # Special Features
    TILT_CONTROL = "tilt_control"  # tilt, otau, otal
    CONTINUOUS_MONITORING = "continuous_monitoring"  # rhtm


@dataclass
class DeviceCapabilities:
    """Container for discovered device capabilities."""

    discovered_capabilities: Set[DeviceCapability]
    status_fields: Set[str]
    environmental_fields: Set[str]
    device_type_hint: Optional[str] = None
    confidence_score: float = 0.0

    def has_capability(self, capability: DeviceCapability) -> bool:
        """Check if device has a specific capability."""
        return capability in self.discovered_capabilities

    def has_any_capability(self, capabilities: List[DeviceCapability]) -> bool:
        """Check if device has any of the given capabilities."""
        return bool(self.discovered_capabilities & set(capabilities))

    def has_all_capabilities(self, capabilities: List[DeviceCapability]) -> bool:
        """Check if device has all of the given capabilities."""
        return set(capabilities).issubset(self.discovered_capabilities)


class CapabilityDetector(ABC):
    """Abstract base class for capability detectors."""

    @abstractmethod
    def detect(
        self, status_data: Dict[str, Any], environmental_data: Dict[str, Any]
    ) -> Set[DeviceCapability]:
        """Detect capabilities from device data."""
        pass

    @abstractmethod
    def get_required_fields(self) -> Set[str]:
        """Get the fields required to detect this capability."""
        pass

    @abstractmethod
    def get_confidence_score(
        self, status_data: Dict[str, Any], environmental_data: Dict[str, Any]
    ) -> float:
        """Get confidence score for this detection (0.0 to 1.0)."""
        pass


class BasicFanDetector(CapabilityDetector):
    """Detects basic fan capabilities."""

    def detect(
        self, status_data: Dict[str, Any], environmental_data: Dict[str, Any]
    ) -> Set[DeviceCapability]:
        capabilities = set()

        # Check for basic fan control fields
        if self._has_fields(status_data, ["fpwr", "fnsp"]):
            capabilities.add(DeviceCapability.BASIC_FAN_CONTROL)

        # Check for basic oscillation
        if self._has_field(status_data, "oson"):
            capabilities.add(DeviceCapability.BASIC_OSCILLATION)

        # Check for night mode
        if self._has_fields(status_data, ["nmod", "nmdv"]):
            capabilities.add(DeviceCapability.NIGHT_MODE)

        # Check for sleep timer
        if self._has_field(status_data, "sltm"):
            capabilities.add(DeviceCapability.SLEEP_TIMER)

        return capabilities

    def get_required_fields(self) -> Set[str]:
        return {"fpwr", "fnsp", "oson", "nmod", "nmdv", "sltm"}

    def get_confidence_score(
        self, status_data: Dict[str, Any], environmental_data: Dict[str, Any]
    ) -> float:
        basic_fields = ["fpwr", "fnsp"]
        oscillation_field = "oson"

        confidence = 0.0

        # High confidence if basic fan fields are present
        if all(self._has_field(status_data, field) for field in basic_fields):
            confidence += 0.8

        # Additional confidence for oscillation
        if self._has_field(status_data, oscillation_field):
            confidence += 0.15

        # Small bonus for additional features
        if self._has_field(status_data, "sltm"):  # Sleep timer
            confidence += 0.05

        return min(1.0, confidence)

    def _has_field(self, data: Dict[str, Any], field: str) -> bool:
        """Check if field exists and has a non-null value."""
        return field in data and data[field] is not None

    def _has_fields(self, data: Dict[str, Any], fields: List[str]) -> bool:
        """Check if all fields exist and have non-null values."""
        return all(self._has_field(data, field) for field in fields)


class AdvancedOscillationDetector(CapabilityDetector):
    """Detects advanced oscillation capabilities with angle control."""

    def detect(
        self, status_data: Dict[str, Any], environmental_data: Dict[str, Any]
    ) -> Set[DeviceCapability]:
        capabilities = set()

        # Check for angle oscillation (osal, osau, ancp)
        if self._has_fields(status_data, ["osal", "osau"]):
            capabilities.add(DeviceCapability.ANGLE_OSCILLATION)

        return capabilities

    def get_required_fields(self) -> Set[str]:
        return {"osal", "osau", "ancp"}

    def get_confidence_score(
        self, status_data: Dict[str, Any], environmental_data: Dict[str, Any]
    ) -> float:
        angle_fields = ["osal", "osau"]

        # Very high confidence if angle oscillation fields are present
        # This is a strong distinguishing feature for AM series
        if self._has_fields(status_data, angle_fields):
            return 0.95

        # Lower confidence if only some angle fields present
        if any(self._has_field(status_data, field) for field in angle_fields):
            return 0.5

        return 0.0

    def _has_field(self, data: Dict[str, Any], field: str) -> bool:
        return field in data and data[field] is not None

    def _has_fields(self, data: Dict[str, Any], fields: List[str]) -> bool:
        return all(self._has_field(data, field) for field in fields)


class PurificationDetector(CapabilityDetector):
    """Detects air purification capabilities."""

    def detect(
        self, status_data: Dict[str, Any], environmental_data: Dict[str, Any]
    ) -> Set[DeviceCapability]:
        capabilities = set()

        # Auto mode for purification
        if self._has_field(status_data, "auto"):
            capabilities.add(DeviceCapability.AUTO_MODE)

        # Filter monitoring
        if self._has_field(status_data, "cflr") or self._has_field(status_data, "hflr"):
            capabilities.add(DeviceCapability.FILTER_MONITORING)

        # PM sensors
        pm_fields = ["p25r", "p10r", "pm25", "pm10"]
        if any(self._has_field(environmental_data, field) for field in pm_fields):
            capabilities.add(DeviceCapability.PM_SENSORS)

        # Front airflow control
        if self._has_field(status_data, "fdir"):
            capabilities.add(DeviceCapability.FRONT_AIRFLOW)

        return capabilities

    def get_required_fields(self) -> Set[str]:
        return {"auto", "cflr", "hflr", "fdir", "p25r", "p10r", "pm25", "pm10"}

    def get_confidence_score(
        self, status_data: Dict[str, Any], environmental_data: Dict[str, Any]
    ) -> float:
        confidence = 0.0

        # Core purification indicators
        if self._has_field(status_data, "auto"):
            confidence += 0.4  # Auto mode is strong indicator

        if self._has_field(status_data, "cflr") or self._has_field(status_data, "hflr"):
            confidence += 0.4  # Filter monitoring is strong indicator

        # PM sensors
        pm_fields = ["pm25", "pm10", "p25r", "p10r"]
        if any(self._has_field(environmental_data, field) for field in pm_fields):
            confidence += 0.3  # Environmental monitoring

        # Airflow control
        if self._has_field(status_data, "fdir"):
            confidence += 0.1

        return min(1.0, confidence)

    def _has_field(self, data: Dict[str, Any], field: str) -> bool:
        return field in data and data[field] is not None

    def _has_fields(self, data: Dict[str, Any], fields: List[str]) -> bool:
        return all(self._has_field(data, field) for field in fields)


class AdvancedEnvironmentalDetector(CapabilityDetector):
    """Detects advanced environmental monitoring capabilities."""

    def detect(
        self, status_data: Dict[str, Any], environmental_data: Dict[str, Any]
    ) -> Set[DeviceCapability]:
        capabilities = set()

        # VOC sensor
        if self._has_field(environmental_data, "va10"):
            capabilities.add(DeviceCapability.VOC_SENSOR)

        # NO2 sensor
        if self._has_field(environmental_data, "noxl"):
            capabilities.add(DeviceCapability.NO2_SENSOR)

        # CO2 sensor
        if self._has_field(environmental_data, "co2r"):
            capabilities.add(DeviceCapability.CO2_SENSOR)

        # Humidity sensor
        if self._has_field(environmental_data, "hact"):
            capabilities.add(DeviceCapability.HUMIDITY_SENSOR)

        # Temperature sensor
        if self._has_field(environmental_data, "tact"):
            capabilities.add(DeviceCapability.TEMPERATURE_SENSOR)

        return capabilities

    def get_required_fields(self) -> Set[str]:
        return {"va10", "noxl", "co2r", "hact", "tact"}

    def get_confidence_score(
        self, status_data: Dict[str, Any], environmental_data: Dict[str, Any]
    ) -> float:
        advanced_fields = ["va10", "noxl", "co2r"]
        detected_count = sum(
            1 for field in advanced_fields if self._has_field(environmental_data, field)
        )
        return detected_count / len(advanced_fields)

    def _has_field(self, data: Dict[str, Any], field: str) -> bool:
        return field in data and data[field] is not None


class HeatingDetector(CapabilityDetector):
    """Detects heating capabilities."""

    def detect(
        self, status_data: Dict[str, Any], environmental_data: Dict[str, Any]
    ) -> Set[DeviceCapability]:
        capabilities = set()

        # Check for heating mode
        if self._has_field(status_data, "hmod"):
            capabilities.add(DeviceCapability.HEATING)

        return capabilities

    def get_required_fields(self) -> Set[str]:
        return {"hmod", "hmax"}

    def get_confidence_score(
        self, status_data: Dict[str, Any], environmental_data: Dict[str, Any]
    ) -> float:
        if self._has_field(status_data, "hmod"):
            return 1.0
        return 0.0

    def _has_field(self, data: Dict[str, Any], field: str) -> bool:
        return field in data and data[field] is not None


class HumidificationDetector(CapabilityDetector):
    """Detects humidification capabilities."""

    def detect(
        self, status_data: Dict[str, Any], environmental_data: Dict[str, Any]
    ) -> Set[DeviceCapability]:
        capabilities = set()

        # Check for humidification
        if self._has_field(status_data, "hume"):
            capabilities.add(DeviceCapability.HUMIDIFICATION)

        # Check for water hardness
        if self._has_field(status_data, "wath"):
            capabilities.add(DeviceCapability.WATER_HARDNESS)

        return capabilities

    def get_required_fields(self) -> Set[str]:
        return {"hume", "haut", "humt", "wath"}

    def get_confidence_score(
        self, status_data: Dict[str, Any], environmental_data: Dict[str, Any]
    ) -> float:
        if self._has_field(status_data, "hume"):
            return 1.0
        return 0.0

    def _has_field(self, data: Dict[str, Any], field: str) -> bool:
        return field in data and data[field] is not None


class DeviceCapabilityDiscovery:
    """Main class for discovering device capabilities dynamically."""

    def __init__(self):
        self.detectors: List[CapabilityDetector] = [
            BasicFanDetector(),
            AdvancedOscillationDetector(),
            PurificationDetector(),
            AdvancedEnvironmentalDetector(),
            HeatingDetector(),
            HumidificationDetector(),
        ]

    def discover_capabilities(
        self, status_data: Dict[str, Any], environmental_data: Dict[str, Any]
    ) -> DeviceCapabilities:
        """Discover all capabilities from device data."""

        all_capabilities = set()
        status_fields = set(status_data.keys()) if status_data else set()
        environmental_fields = (
            set(environmental_data.keys()) if environmental_data else set()
        )

        # Run all detectors and collect results
        detector_results = []
        for detector in self.detectors:
            try:
                capabilities = detector.detect(status_data, environmental_data)
                confidence = detector.get_confidence_score(
                    status_data, environmental_data
                )

                detector_results.append(
                    {
                        "detector": detector.__class__.__name__,
                        "capabilities": capabilities,
                        "confidence": confidence,
                        "is_relevant": len(capabilities) > 0 or confidence > 0.0,
                    }
                )

                all_capabilities.update(capabilities)

                _LOGGER.debug(
                    f"{detector.__class__.__name__} detected: {capabilities} (confidence: {confidence})"
                )

            except Exception as e:
                _LOGGER.warning(f"Error in {detector.__class__.__name__}: {e}")

        # Calculate intelligent overall confidence
        overall_confidence = self._calculate_intelligent_confidence(
            detector_results, all_capabilities
        )

        # Suggest device type based on capabilities
        device_type_hint = self._suggest_device_type(all_capabilities)

        return DeviceCapabilities(
            discovered_capabilities=all_capabilities,
            status_fields=status_fields,
            environmental_fields=environmental_fields,
            device_type_hint=device_type_hint,
            confidence_score=overall_confidence,
        )

    def _suggest_device_type(self, capabilities: Set[DeviceCapability]) -> str:
        """Suggest appropriate device type based on discovered capabilities."""

        # Advanced purifier with full environmental monitoring
        if capabilities & {
            DeviceCapability.VOC_SENSOR,
            DeviceCapability.NO2_SENSOR,
            DeviceCapability.CO2_SENSOR,
        }:
            # Check if it also has heating or humidification
            if DeviceCapability.HEATING in capabilities:
                return "AdvancedPurifierFanWithHeating"
            elif DeviceCapability.HUMIDIFICATION in capabilities:
                return "AdvancedPurifierFanWithHumidification"
            else:
                return "AdvancedPurifierFan"

        # Special combination devices with basic purification
        elif (
            DeviceCapability.HEATING in capabilities
            and DeviceCapability.AUTO_MODE in capabilities
        ):
            # Basic purifier with heating (HP series like HP04, HP07, HP09)
            return "BasicPurifierFanWithHeating"

        elif (
            DeviceCapability.HUMIDIFICATION in capabilities
            and DeviceCapability.AUTO_MODE in capabilities
        ):
            # Basic purifier with humidification (PH series like PH01, PH02, PH03, PH04)
            return "BasicPurifierFanWithHumidification"

        # Basic purifier with air purification but no advanced sensors
        elif capabilities & {
            DeviceCapability.AUTO_MODE,
            DeviceCapability.FILTER_MONITORING,
        }:
            if DeviceCapability.ANGLE_OSCILLATION in capabilities:
                return "BasicPurifierFanWithOscillation"
            else:
                return "BasicPurifierFan"

        # Basic fan with advanced oscillation
        elif DeviceCapability.ANGLE_OSCILLATION in capabilities:
            return "AdvancedOscillationFan"

        # Basic fan only
        elif DeviceCapability.BASIC_FAN_CONTROL in capabilities:
            return "BasicFan"

        # Unknown device
        else:
            return "UnknownDevice"

    def _calculate_intelligent_confidence(
        self, detector_results: List[Dict], all_capabilities: Set[DeviceCapability]
    ) -> float:
        """Calculate confidence based on relevant detectors and capability coherence."""

        if not detector_results:
            return 0.0

        # Get results from relevant detectors (those that found something or have confidence > 0)
        relevant_results = [r for r in detector_results if r["is_relevant"]]

        if not relevant_results:
            return 0.0

        # Calculate weighted confidence based on detector importance and results
        total_weighted_confidence = 0.0
        total_weight = 0.0

        for result in relevant_results:
            detector_name = result["detector"]
            confidence = result["confidence"]
            capabilities_found = len(result["capabilities"])

            # Assign weights based on detector importance and findings
            if detector_name == "BasicFanDetector":
                # Core detector - high weight if it finds basic fan capabilities
                weight = 3.0 if capabilities_found > 0 else 1.0
            elif detector_name == "AdvancedOscillationDetector":
                # Specialized detector - high confidence when it detects something
                weight = 2.5 if capabilities_found > 0 else 0.5
            elif detector_name == "PurificationDetector":
                # Important for classification - high weight for purifiers
                weight = 3.0 if capabilities_found > 0 else 1.0
            elif detector_name == "AdvancedEnvironmentalDetector":
                # Distinguishes advanced vs basic purifiers - high weight
                weight = 2.5 if capabilities_found > 0 else 0.5
            elif detector_name in ["HeatingDetector", "HumidificationDetector"]:
                # Specialized feature detectors - high confidence when they detect
                weight = 2.0 if capabilities_found > 0 else 0.5
            else:
                weight = 1.0

            weighted_confidence = confidence * weight
            total_weighted_confidence += weighted_confidence
            total_weight += weight

        base_confidence = (
            total_weighted_confidence / total_weight if total_weight > 0 else 0.0
        )

        # Apply coherence bonus based on capability patterns
        coherence_bonus = self._calculate_coherence_bonus(all_capabilities)

        # Combine base confidence with coherence bonus
        final_confidence = min(1.0, base_confidence + coherence_bonus)

        return final_confidence

    def _calculate_coherence_bonus(self, capabilities: Set[DeviceCapability]) -> float:
        """Calculate bonus confidence based on logical capability combinations."""

        bonus = 0.0

        # Strong coherence patterns that increase confidence

        # Pattern 1: Complete basic fan setup
        if {
            DeviceCapability.BASIC_FAN_CONTROL,
            DeviceCapability.BASIC_OSCILLATION,
        }.issubset(capabilities):
            bonus += 0.1

        # Pattern 2: Complete purification setup
        if {
            DeviceCapability.AUTO_MODE,
            DeviceCapability.FILTER_MONITORING,
            DeviceCapability.PM_SENSORS,
        }.issubset(capabilities):
            bonus += 0.15

        # Pattern 3: Advanced environmental monitoring suite
        advanced_sensors = {
            DeviceCapability.VOC_SENSOR,
            DeviceCapability.NO2_SENSOR,
            DeviceCapability.CO2_SENSOR,
        }
        if (
            len(advanced_sensors & capabilities) >= 2
        ):  # At least 2 of 3 advanced sensors
            bonus += 0.2

        # Pattern 4: Specialized device combinations
        if (
            DeviceCapability.HEATING in capabilities
            and DeviceCapability.AUTO_MODE in capabilities
        ):
            bonus += 0.15  # Hot+Cool makes sense

        if (
            DeviceCapability.HUMIDIFICATION in capabilities
            and DeviceCapability.HUMIDITY_SENSOR in capabilities
        ):
            bonus += 0.15  # Humidify+Cool makes sense

        # Pattern 5: Angle oscillation specificity (AM series marker)
        if DeviceCapability.ANGLE_OSCILLATION in capabilities:
            if DeviceCapability.AUTO_MODE not in capabilities:  # Pure fan, not purifier
                bonus += 0.2  # High confidence for AM series detection

        # Pattern 6: Environmental sensor completeness
        environmental_sensors = {
            DeviceCapability.HUMIDITY_SENSOR,
            DeviceCapability.TEMPERATURE_SENSOR,
        }
        if environmental_sensors.issubset(capabilities):
            bonus += 0.1

        return min(0.3, bonus)  # Cap bonus at 30%
