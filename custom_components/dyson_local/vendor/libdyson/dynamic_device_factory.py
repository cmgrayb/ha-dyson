"""Dynamic Device Factory using capability discovery."""

import logging
from typing import Any, Dict, Optional

from .capability_discovery import DeviceCapability, DeviceCapabilityDiscovery
from .dyson_advanced_oscillation_fan import DysonAdvancedOscillationFan
from .dyson_advanced_purifier_fan import DysonAdvancedPurifierFan
from .dyson_basic_fan import DysonBasicFan
from .dyson_basic_purifier_fan import DysonBasicPurifierFanWithOscillation
from .dyson_basic_purifier_fan_with_heating import DysonBasicPurifierFanWithHeating
from .dyson_basic_purifier_fan_with_humidification import (
    DysonBasicPurifierFanWithHumidification,
)
from .dyson_device import DysonDevice

_LOGGER = logging.getLogger(__name__)


class DynamicDeviceFactory:
    """Factory for creating Dyson devices based on discovered capabilities."""

    def __init__(self):
        self.capability_discovery = DeviceCapabilityDiscovery()

    def create_device_from_capabilities(
        self,
        serial: str,
        credential: str,
        device_type: str,
        status_data: Optional[Dict[str, Any]] = None,
        environmental_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[DysonDevice]:
        """
        Create a device instance based on discovered capabilities.

        Args:
            serial: Device serial number
            credential: Device credential
            device_type: Device type code (for fallback/logging)
            status_data: Current device status data
            environmental_data: Current environmental sensor data

        Returns:
            Appropriate device instance or None if creation fails
        """

        # If we don't have data to analyze, fall back to static mapping
        if not status_data and not environmental_data:
            _LOGGER.warning(
                f"No data available for capability discovery of device {serial}, using static mapping"
            )
            return self._fallback_to_static_mapping(serial, credential, device_type)

        # Discover capabilities
        capabilities = self.capability_discovery.discover_capabilities(
            status_data or {}, environmental_data or {}
        )

        _LOGGER.info(
            f"Device {serial} capabilities discovered: {capabilities.discovered_capabilities}"
        )
        _LOGGER.info(
            f"Suggested device type: {capabilities.device_type_hint} (confidence: {capabilities.confidence_score:.2f})"
        )

        # Create device based on discovered capabilities
        device_instance = self._create_device_from_capabilities(
            serial, credential, device_type, capabilities
        )

        if device_instance:
            # Store capability information for debugging
            device_instance._discovered_capabilities = capabilities
            _LOGGER.info(
                f"Created {type(device_instance).__name__} for device {serial}"
            )
        else:
            _LOGGER.warning(
                f"Failed to create device for {serial}, falling back to static mapping"
            )
            device_instance = self._fallback_to_static_mapping(
                serial, credential, device_type
            )

        return device_instance

    def _create_device_from_capabilities(
        self, serial: str, credential: str, device_type: str, capabilities
    ) -> Optional[DysonDevice]:
        """Create device instance based on discovered capabilities."""

        # Advanced Purifier (BP series) - has VOC, NO2, CO2 sensors
        if capabilities.has_any_capability(
            [
                DeviceCapability.VOC_SENSOR,
                DeviceCapability.NO2_SENSOR,
                DeviceCapability.CO2_SENSOR,
            ]
        ):
            _LOGGER.debug(
                f"Creating AdvancedPurifierFan for {serial} - has advanced environmental sensors"
            )
            return DysonAdvancedPurifierFan(serial, credential, device_type)

        # Basic Purifier with heating (HP series) - has purification + heating but no advanced sensors
        elif (
            capabilities.has_capability(DeviceCapability.AUTO_MODE)
            and capabilities.has_capability(DeviceCapability.FILTER_MONITORING)
            and capabilities.has_capability(DeviceCapability.HEATING)
        ):
            _LOGGER.debug(
                f"Creating BasicPurifierFanWithHeating for {serial} - has basic purification + heating"
            )
            return DysonBasicPurifierFanWithHeating(serial, credential, device_type)

        # Basic Purifier with humidification (PH series) - has purification + humidification but no advanced sensors
        elif (
            capabilities.has_capability(DeviceCapability.AUTO_MODE)
            and capabilities.has_capability(DeviceCapability.FILTER_MONITORING)
            and capabilities.has_capability(DeviceCapability.HUMIDIFICATION)
        ):
            _LOGGER.debug(
                f"Creating BasicPurifierFanWithHumidification for {serial} - has basic purification + humidification"
            )
            return DysonBasicPurifierFanWithHumidification(
                serial, credential, device_type
            )

        # Basic Purifier with oscillation (TP04/TP07/TP09/TP11) - has purification but no heating/humidification or advanced sensors
        elif capabilities.has_capability(
            DeviceCapability.AUTO_MODE
        ) and capabilities.has_capability(DeviceCapability.FILTER_MONITORING):
            _LOGGER.debug(
                f"Creating BasicPurifierFanWithOscillation for {serial} - has basic purification"
            )
            return DysonBasicPurifierFanWithOscillation(serial, credential, device_type)

        # Advanced Oscillation Fan (AM12) - has angle oscillation but no purification
        elif capabilities.has_capability(
            DeviceCapability.ANGLE_OSCILLATION
        ) and not capabilities.has_capability(DeviceCapability.AUTO_MODE):
            _LOGGER.debug(
                f"Creating AdvancedOscillationFan for {serial} - has angle oscillation, no purification"
            )
            return DysonAdvancedOscillationFan(serial, credential, device_type)

        # Basic Fan - just basic fan controls
        elif capabilities.has_capability(DeviceCapability.BASIC_FAN_CONTROL):
            _LOGGER.debug(f"Creating BasicFan for {serial} - basic fan controls only")
            return DysonBasicFan(serial, credential, device_type)

        else:
            _LOGGER.warning(
                f"Could not determine appropriate device class for {serial} with capabilities: {capabilities.discovered_capabilities}"
            )
            return None

    def _fallback_to_static_mapping(
        self, serial: str, credential: str, device_type: str
    ) -> Optional[DysonDevice]:
        """Fallback to static device type mapping when capability discovery fails."""
        _LOGGER.info(f"Using static mapping for device type {device_type}")

        # Direct static mapping without recursion - using already imported classes

        # AM12 fallback (739 family)
        if device_type.startswith("739"):
            _LOGGER.debug("Fallback: Creating DysonAdvancedOscillationFan for AM12")
            return DysonAdvancedOscillationFan(serial, credential, device_type)

        # TP series fallback (438 family - handles all regional variants)
        if device_type.startswith("438"):  # Covers 438, 438K, 438E, 438M
            _LOGGER.debug(
                "Fallback: Creating DysonBasicPurifierFanWithOscillation for TP series"
            )
            return DysonBasicPurifierFanWithOscillation(serial, credential, device_type)

        # HP series fallback (527 family - handles all regional variants)
        if device_type.startswith("527"):  # Covers 527, 527E, 527K, 527M
            _LOGGER.debug(
                "Fallback: Creating DysonBasicPurifierFanWithHeating for HP series"
            )
            return DysonBasicPurifierFanWithHeating(serial, credential, device_type)

        # PH series fallback (358 family - handles all regional variants)
        if device_type.startswith("358"):  # Covers 358, 358K, 358E
            _LOGGER.debug(
                "Fallback: Creating DysonBasicPurifierFanWithHumidification for PH series"
            )
            return DysonBasicPurifierFanWithHumidification(
                serial, credential, device_type
            )

        # BP series fallback (664 family)
        if device_type.startswith("664"):  # Covers BP02, BP04
            _LOGGER.debug("Fallback: Creating DysonAdvancedPurifierFan for BP series")
            return DysonAdvancedPurifierFan(serial, credential, device_type)

        _LOGGER.error(
            "Unknown device type: %s for serial: %s. No static mapping available.",
            device_type,
            serial,
        )
        return None

    def get_device_capabilities_summary(self, device: DysonDevice) -> Dict[str, Any]:
        """Get a summary of the device's discovered capabilities."""
        if hasattr(device, "_discovered_capabilities"):
            caps = device._discovered_capabilities
            return {
                "device_class": type(device).__name__,
                "capabilities": [cap.value for cap in caps.discovered_capabilities],
                "confidence_score": caps.confidence_score,
                "suggested_type": caps.device_type_hint,
                "status_fields": list(caps.status_fields),
                "environmental_fields": list(caps.environmental_fields),
            }
        else:
            return {
                "device_class": type(device).__name__,
                "capabilities": "Static mapping used",
                "note": "Device created without capability discovery",
            }


# Create global instance for easy access
dynamic_factory = DynamicDeviceFactory()


def get_device_with_capability_discovery(
    serial: str,
    credential: str,
    device_type: str,
    status_data: Optional[Dict[str, Any]] = None,
    environmental_data: Optional[Dict[str, Any]] = None,
) -> Optional[DysonDevice]:
    """
    Create a Dyson device using capability discovery.

    This is the new dynamic factory function that should eventually replace
    the static get_device() function.

    Args:
        serial: Device serial number
        credential: Device credential
        device_type: Device type code
        status_data: Current device status data
        environmental_data: Current environmental sensor data

    Returns:
        Appropriate device instance based on discovered capabilities
    """
    return dynamic_factory.create_device_from_capabilities(
        serial, credential, device_type, status_data, environmental_data
    )
