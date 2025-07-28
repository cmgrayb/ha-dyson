"""Dyson device info."""

from typing import Optional

import attr

from .utils import decrypt_password


@attr.s(auto_attribs=True, frozen=True)
class DysonDeviceInfo:
    """Dyson device info with complete OpenAPI field support."""

    # Core required fields (existing)
    serial: str
    name: str
    version: str
    credential: str
    auto_update: bool
    new_version_available: bool
    product_type: str

    # Optional legacy field
    active: Optional[bool] = None

    # OpenAPI Device schema fields
    category: Optional[str] = None  # ec, flrc, hc, light, robot, wearable
    connection_category: Optional[str] = (
        None  # lecAndWifi, lecOnly, nonConnected, wifiOnly
    )
    model: Optional[str] = None  # Actual model number (TP04, HP07, etc.)
    type: Optional[str] = None  # MQTT topic prefix (438, 527, etc.)
    variant: Optional[str] = None  # Regional variant (K, E, M, etc.)

    # ConnectedConfiguration fields
    firmware_auto_update_enabled: Optional[bool] = None
    firmware_new_version_available: Optional[bool] = None
    firmware_version: Optional[str] = None
    firmware_capabilities: Optional[list] = None

    # MQTT configuration fields
    mqtt_local_broker_credentials: Optional[str] = None
    mqtt_root_topic_level: Optional[str] = None
    mqtt_remote_broker_type: Optional[str] = None

    # Raw data for debugging/future expansion
    raw_data: Optional[dict] = None

    @classmethod
    def from_raw(cls, raw: dict):
        """Parse raw data from Dyson API with complete OpenAPI field support."""

        # Helper function to safely get nested values
        def safe_get(data, *keys, default=None):
            for key in keys:
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    return default
            return data

        # Extract core required fields
        serial = raw["Serial"]
        name = raw["Name"]
        version = raw["Version"]
        credential = decrypt_password(raw["LocalCredentials"])
        auto_update = raw["AutoUpdate"]
        new_version_available = raw["NewVersionAvailable"]
        product_type = raw["ProductType"]

        # Extract optional legacy field
        active = raw.get("Active")

        # Extract OpenAPI Device schema fields
        category = raw.get("category")
        connection_category = raw.get("connectionCategory")
        model = raw.get("model")
        device_type = raw.get(
            "type"
        )  # 'type' is a Python keyword, so use different var name
        variant = raw.get("variant")

        # Extract ConnectedConfiguration fields
        connected_config = raw.get("connectedConfiguration", {})
        firmware = connected_config.get("firmware", {})
        mqtt_config = connected_config.get("mqtt", {})

        firmware_auto_update_enabled = firmware.get("autoUpdateEnabled")
        firmware_new_version_available = firmware.get("newVersionAvailable")
        firmware_version = firmware.get("version")
        firmware_capabilities = firmware.get("capabilities")

        mqtt_local_broker_credentials = mqtt_config.get("localBrokerCredentials")
        mqtt_root_topic_level = mqtt_config.get("mqttRootTopicLevel")
        mqtt_remote_broker_type = mqtt_config.get("remoteBrokerType")

        return cls(
            serial=serial,
            name=name,
            version=version,
            credential=credential,
            auto_update=auto_update,
            new_version_available=new_version_available,
            product_type=product_type,
            active=active,
            category=category,
            connection_category=connection_category,
            model=model,
            type=device_type,
            variant=variant,
            firmware_auto_update_enabled=firmware_auto_update_enabled,
            firmware_new_version_available=firmware_new_version_available,
            firmware_version=firmware_version,
            firmware_capabilities=firmware_capabilities,
            mqtt_local_broker_credentials=mqtt_local_broker_credentials,
            mqtt_root_topic_level=mqtt_root_topic_level,
            mqtt_remote_broker_type=mqtt_remote_broker_type,
            raw_data=raw,  # Store complete raw data for debugging
        )

    def get_mqtt_device_type(self) -> str:
        """Get the proper MQTT device type for topic formation.

        This method determines the correct device type to use for MQTT topics
        by checking available fields in order of preference:
        1. mqttRootTopicLevel (direct from MQTT config - most reliable!)
        2. type + variant (from OpenAPI fields)
        3. model analysis (extract from model field)
        4. product_type (legacy fallback)

        Returns:
            Device type string for MQTT topics (e.g., "438M", "527E", "438")
        """
        from ..const import construct_device_type

        # First priority: mqttRootTopicLevel from MQTT config
        # This is the actual MQTT topic prefix the device uses!
        if self.mqtt_root_topic_level:
            return self.mqtt_root_topic_level

        # Second priority: OpenAPI type + variant fields
        if self.type:
            return construct_device_type(self.type, self.variant)

        # Third priority: extract from model field if available
        if self.model:
            # Common patterns: TP07, TP04K, HP07E, PH04, etc.
            model = self.model.upper()

            # Extract device type mapping from model
            model_mappings = {
                "TP": "438",  # TP series -> 438
                "HP": "527",  # HP series -> 527
                "PH": "358",  # PH series -> 358
                "AM": "739",  # AM series -> 739
                "BP": "664",  # BP series -> 664
            }

            for prefix, device_type in model_mappings.items():
                if model.startswith(prefix):
                    # Extract variant if present (last character if letter)
                    variant = None
                    if len(model) > 3 and model[-1].isalpha():
                        variant = model[-1]
                    return construct_device_type(device_type, variant)

        # Fourth priority: extract from version field (legacy API format)
        # Version patterns: "438MPF.00.01.003.0011", "527EEU.04.01.025.0045", etc.
        if self.version:
            version = self.version.upper()

            # Extract device type from version string
            # Pattern: starts with device type number, followed by variant letter(s)
            import re

            version_match = re.match(r"^(\d{3})([A-Z]+)", version)
            if version_match:
                device_type = version_match.group(1)
                variant_letters = version_match.group(2)

                # Take first letter as variant (M from MPF, E from EEU, etc.)
                variant = variant_letters[0] if variant_letters else None
                return construct_device_type(device_type, variant)

        # Final fallback to product_type (existing behavior)
        return self.product_type

    def get_display_model(self) -> str:
        """Get human-readable model name."""
        if self.model:
            return self.model

        # Try to derive from other fields
        if self.type and self.variant:
            type_to_series = {
                "438": "TP",
                "527": "HP",
                "358": "PH",
                "739": "AM",
                "664": "BP",
            }
            series = type_to_series.get(self.type, self.type)
            return f"{series}XX{self.variant}"  # e.g., TPXXM, HPXXE

        return self.product_type

    def debug_info(self) -> dict:
        """Get debugging information about device type detection."""

        # Determine the source of MQTT device type
        mqtt_source = "product_type (fallback)"
        if self.mqtt_root_topic_level:
            mqtt_source = "mqttRootTopicLevel (direct)"
        elif self.type:
            mqtt_source = "type+variant (OpenAPI)"
        elif self.model:
            mqtt_source = "model (analyzed)"
        elif self.version:
            # Check if version contains variant info
            import re

            version_match = re.match(r"^(\d{3})([A-Z]+)", self.version.upper())
            if version_match:
                mqtt_source = "version (analyzed)"

        return {
            "serial": self.serial,
            "name": self.name,
            "product_type": self.product_type,
            "openapi_type": self.type,
            "openapi_variant": self.variant,
            "openapi_model": self.model,
            "openapi_category": self.category,
            "mqtt_root_topic_level": self.mqtt_root_topic_level,
            "mqtt_device_type": self.get_mqtt_device_type(),
            "mqtt_source": mqtt_source,
            "display_model": self.get_display_model(),
            "has_raw_data": self.raw_data is not None,
            "raw_keys": list(self.raw_data.keys()) if self.raw_data else [],
        }
