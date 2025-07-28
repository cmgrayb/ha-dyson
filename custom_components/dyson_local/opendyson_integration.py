"""
OpenDyson integration module for enhanced MQTT topic determination.

This module provides a minimal adapter to integrate OpenDyson's superior
MQTT topic determination approach into the existing Home Assistant integration
without requiring major architectural changes.
"""

import logging
from typing import Optional

from .vendor.libdyson import get_device
from .vendor.libdyson.cloud.device_info import DysonDeviceInfo
from .vendor.libdyson.dyson_device import DysonDevice

_LOGGER = logging.getLogger(__name__)


class OpenDysonStyleDeviceFactory:
    """
    Minimal adapter to use OpenDyson's MQTT topic determination approach.

    This addresses the user's request to "replicate the discovery mechanism
    for devices that opendyson has accomplished" specifically for MQTT topic
    determination.
    """

    def create_device_with_opendyson_mqtt_topic(
        self,
        device_info: DysonDeviceInfo,
        serial: Optional[str] = None,
        credential: Optional[str] = None,
    ) -> Optional[DysonDevice]:
        """
        Create device using OpenDyson's MQTT topic determination approach.

        This is the key enhancement that addresses MQTT topic issues,
        especially for TP series devices with regional variants.

        Args:
            device_info: DysonDeviceInfo object from cloud API
            serial: Override serial (defaults to device_info.serial)
            credential: Override credential (defaults to device_info.credential)

        Returns:
            DysonDevice instance or None if creation failed
        """
        # Step 1: Get MQTT topic using OpenDyson's priority system
        mqtt_topic_root = device_info.get_mqtt_device_type()
        debug_info = device_info.debug_info()

        # Step 2: Log the source for debugging
        _LOGGER.info(
            f"Device {device_info.serial}: MQTT topic '{mqtt_topic_root}' "
            f"from {debug_info['mqtt_source']}"
        )

        # Step 3: Create device using the correct MQTT topic
        device = get_device(
            serial or device_info.serial,
            credential or device_info.credential,
            mqtt_topic_root,  # This is the key change - use OpenDyson's determination!
        )

        if device:
            # Store OpenDyson-style debug information for troubleshooting
            device._mqtt_topic_source = debug_info["mqtt_source"]
            device._original_device_info = device_info

            _LOGGER.info(
                f"Created {type(device).__name__} for {device_info.serial} "
                f"with MQTT topic: {mqtt_topic_root}"
            )

            # Log example MQTT topics for debugging
            _LOGGER.debug(
                f"Example MQTT topics for {device_info.serial}:\n"
                f"  Status: {mqtt_topic_root}/{device_info.serial}/status/current\n"
                f"  Command: {mqtt_topic_root}/{device_info.serial}/command\n"
                f"  Fault: {mqtt_topic_root}/{device_info.serial}/status/fault"
            )
        else:
            _LOGGER.error(
                f"Failed to create device for {device_info.serial} "
                f"using MQTT topic: {mqtt_topic_root}"
            )

        return device


def debug_mqtt_topic_determination(device_info: DysonDeviceInfo) -> dict:
    """
    Helper function to debug MQTT topic determination issues.

    This is especially useful for TP series devices that may have
    MQTT communication problems due to incorrect topic determination.
    """
    try:
        mqtt_topic = device_info.get_mqtt_device_type()
        debug_info = device_info.debug_info()

        analysis = {
            "serial": device_info.serial,
            "determined_mqtt_topic": mqtt_topic,
            "topic_source": debug_info["mqtt_source"],
            "is_opendyson_approach": getattr(device_info, "mqtt_root_topic_level", None)
            is not None,
            "cloud_api_fields": {
                "mqtt_root_topic_level": getattr(
                    device_info, "mqtt_root_topic_level", None
                ),
                "product_type": device_info.product_type,
                "variant": device_info.variant,
                "firmware_version": device_info.version,
            },
            "example_topics": {
                "status": f"{mqtt_topic}/{device_info.serial}/status/current",
                "command": f"{mqtt_topic}/{device_info.serial}/command",
                "fault": f"{mqtt_topic}/{device_info.serial}/status/fault",
            },
        }

        # Log analysis for debugging
        _LOGGER.info(f"MQTT Topic Analysis for {device_info.serial}:")
        for key, value in analysis.items():
            if isinstance(value, dict):
                _LOGGER.info(f"  {key}:")
                for sub_key, sub_value in value.items():
                    _LOGGER.info(f"    {sub_key}: {sub_value}")
            else:
                _LOGGER.info(f"  {key}: {value}")

        return analysis

    except Exception as e:
        _LOGGER.error(
            f"Error in debug_mqtt_topic_determination for {device_info.serial}: {e}"
        )
        # Return a minimal analysis with error information
        return {
            "serial": device_info.serial,
            "error": str(e),
            "determined_mqtt_topic": device_info.product_type,  # Safe fallback
            "topic_source": "error_fallback",
        }


def validate_opendyson_mqtt_setup(devices: list[DysonDeviceInfo]) -> dict:
    """
    Validate that devices are properly configured for OpenDyson-style MQTT topics.

    Returns a summary showing which devices are using optimal MQTT topic determination.
    """
    summary = {
        "total_devices": len(devices),
        "using_direct_mqtt_topic": 0,
        "using_fallback_methods": 0,
        "tp_series_devices": [],
        "potential_issues": [],
    }

    for device_info in devices:
        try:
            debug_info = device_info.debug_info()
            mqtt_root_topic_level = getattr(device_info, "mqtt_root_topic_level", None)

            if mqtt_root_topic_level:
                summary["using_direct_mqtt_topic"] += 1
            else:
                summary["using_fallback_methods"] += 1

                # Flag potential TP series issues based on product_type
                if device_info.product_type and device_info.product_type.startswith(
                    "TP"
                ):
                    summary["tp_series_devices"].append(
                        {
                            "serial": device_info.serial,
                            "product_type": device_info.product_type,
                            "mqtt_topic": device_info.get_mqtt_device_type(),
                            "source": debug_info["mqtt_source"],
                        }
                    )

                    if debug_info["mqtt_source"] == "product_type (fallback)":
                        summary["potential_issues"].append(
                            f"TP device {device_info.serial} using fallback method - "
                            f"may have MQTT communication issues"
                        )
        except Exception as e:
            _LOGGER.error(f"Error validating device {device_info.serial}: {e}")
            summary["using_fallback_methods"] += 1

    _LOGGER.info("OpenDyson MQTT Setup Validation Summary:")
    _LOGGER.info(f"Total devices: {summary['total_devices']}")
    _LOGGER.info(
        f"Using direct MQTT topic (optimal): {summary['using_direct_mqtt_topic']}"
    )
    _LOGGER.info(f"Using fallback methods: {summary['using_fallback_methods']}")

    if summary["potential_issues"]:
        _LOGGER.warning("Potential MQTT topic issues found:")
        for issue in summary["potential_issues"]:
            _LOGGER.warning(f"  - {issue}")

    return summary


# Global factory instance for reuse
_opendyson_factory = None


def get_opendyson_factory() -> OpenDysonStyleDeviceFactory:
    """Get a shared instance of the OpenDyson factory."""
    global _opendyson_factory
    if _opendyson_factory is None:
        _opendyson_factory = OpenDysonStyleDeviceFactory()
    return _opendyson_factory
