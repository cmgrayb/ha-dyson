"""Progressive discovery manager for Dyson devices."""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional, Set

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    from .vendor.libdyson import DysonDevice

_LOGGER = logging.getLogger(__name__)


class ProgressiveDiscoveryManager:
    """Manages progressive discovery for Dyson devices.

    This class monitors MQTT data to enhance device capabilities over time,
    allowing entities to be created immediately with basic functionality and
    then enhanced as more MQTT data becomes available.
    """

    def __init__(
        self, hass: "HomeAssistant", device: "DysonDevice", entry: "ConfigEntry"
    ) -> None:
        """Initialize the progressive discovery manager."""
        self.hass = hass
        self.device = device
        self.entry = entry
        self._logger = logging.getLogger(f"{__name__}.{device.serial}")

        # Track discovered capabilities
        self._discovered_capabilities: Set[str] = set()
        self._last_status_data: Optional[Dict[str, Any]] = None
        self._last_environmental_data: Optional[Dict[str, Any]] = None

        # Control monitoring state
        self._monitoring = False
        self._message_listener_added = False

        self._logger.debug(
            "Progressive discovery manager initialized for device %s", device.serial
        )

    async def start_monitoring(self) -> None:
        """Start monitoring MQTT data for capability discovery."""
        if self._monitoring:
            self._logger.debug("Progressive discovery already monitoring")
            return

        self._logger.info(
            "Starting progressive discovery monitoring for device %s",
            self.device.serial,
        )
        self._monitoring = True

        # Add MQTT message listener to monitor incoming data
        if (
            hasattr(self.device, "add_message_listener")
            and not self._message_listener_added
        ):
            self.device.add_message_listener(self._on_mqtt_message)
            self._message_listener_added = True
            self._logger.debug("Added MQTT message listener for progressive discovery")

        # Schedule initial capability analysis
        await self._analyze_current_capabilities()

    async def stop_monitoring(self) -> None:
        """Stop monitoring MQTT data."""
        if not self._monitoring:
            return

        self._logger.info(
            "Stopping progressive discovery monitoring for device %s",
            self.device.serial,
        )
        self._monitoring = False

        # Remove MQTT message listener
        if (
            hasattr(self.device, "remove_message_listener")
            and self._message_listener_added
        ):
            self.device.remove_message_listener(self._on_mqtt_message)
            self._message_listener_added = False
            self._logger.debug("Removed MQTT message listener")

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._logger.debug(
            "Cleaning up progressive discovery manager for device %s",
            self.device.serial,
        )

        # Ensure monitoring is stopped
        if self._monitoring:
            await self.stop_monitoring()

    async def _on_mqtt_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming MQTT messages for capability discovery."""
        if not self._monitoring:
            return

        message_type = message.get("msg", "")

        try:
            if message_type == "CURRENT-STATE":
                await self._process_status_data(message)
            elif message_type == "ENVIRONMENTAL-CURRENT-SENSOR-DATA":
                await self._process_environmental_data(message)
            elif message_type == "STATE-CHANGE":
                await self._process_state_change(message)

        except Exception as e:
            self._logger.warning(
                "Error processing MQTT message for progressive discovery: %s", str(e)
            )

    async def _process_status_data(self, message: Dict[str, Any]) -> None:
        """Process status data to discover new capabilities."""
        product_state = message.get("product-state", {})

        if not product_state:
            return

        # Store the latest status data
        self._last_status_data = product_state

        # Analyze for new capabilities
        new_capabilities = await self._discover_capabilities_from_status(product_state)

        if new_capabilities:
            self._logger.info(
                "Progressive discovery found new capabilities for %s: %s",
                self.device.serial,
                new_capabilities,
            )
            await self._enhance_device_capabilities(new_capabilities)

    async def _process_environmental_data(self, message: Dict[str, Any]) -> None:
        """Process environmental sensor data to discover new capabilities."""
        data = message.get("data", {})

        if not data:
            return

        # Store the latest environmental data
        self._last_environmental_data = data

        # Analyze for sensor capabilities
        new_sensors = await self._discover_sensor_capabilities(data)

        if new_sensors:
            self._logger.info(
                "Progressive discovery found new sensors for %s: %s",
                self.device.serial,
                new_sensors,
            )
            await self._enhance_sensor_capabilities(new_sensors)

    async def _process_state_change(self, message: Dict[str, Any]) -> None:
        """Process state change messages to understand device behavior."""
        product_state = message.get("product-state", {})

        if not product_state:
            return

        # Analyze state changes to understand device capabilities
        await self._analyze_state_transitions(product_state)

    async def _discover_capabilities_from_status(
        self, product_state: Dict[str, Any]
    ) -> Set[str]:
        """Discover device capabilities from status data."""
        new_capabilities = set()

        # Oscillation capabilities
        if (
            "oscs" in product_state
            and "oscillation" not in self._discovered_capabilities
        ):
            new_capabilities.add("oscillation")

        if (
            all(key in product_state for key in ["osal", "osau"])
            and "oscillation_angles" not in self._discovered_capabilities
        ):
            new_capabilities.add("oscillation_angles")

        # Fan capabilities
        if (
            "fnsp" in product_state
            and "fan_speed_control" not in self._discovered_capabilities
        ):
            new_capabilities.add("fan_speed_control")

        if "auto" in product_state and "auto_mode" not in self._discovered_capabilities:
            new_capabilities.add("auto_mode")

        # Heating capabilities
        if "hflr" in product_state and "heating" not in self._discovered_capabilities:
            new_capabilities.add("heating")

        # Night mode capabilities
        if (
            "nmod" in product_state
            and "night_mode" not in self._discovered_capabilities
        ):
            new_capabilities.add("night_mode")

        # Timer capabilities
        if (
            "sltm" in product_state
            and "sleep_timer" not in self._discovered_capabilities
        ):
            new_capabilities.add("sleep_timer")

        # Filter capabilities
        if (
            any(key in product_state for key in ["cflt", "hflt"])
            and "filter_status" not in self._discovered_capabilities
        ):
            new_capabilities.add("filter_status")

        # Update discovered capabilities
        self._discovered_capabilities.update(new_capabilities)

        return new_capabilities

    async def _discover_sensor_capabilities(self, data: Dict[str, Any]) -> Set[str]:
        """Discover sensor capabilities from environmental data."""
        new_sensors = set()

        # Air quality sensors
        if "pm25" in data and "pm25_sensor" not in self._discovered_capabilities:
            new_sensors.add("pm25_sensor")

        if "pm10" in data and "pm10_sensor" not in self._discovered_capabilities:
            new_sensors.add("pm10_sensor")

        # Humidity sensor
        if "hact" in data and "humidity_sensor" not in self._discovered_capabilities:
            new_sensors.add("humidity_sensor")

        # Temperature sensor
        if "tact" in data and "temperature_sensor" not in self._discovered_capabilities:
            new_sensors.add("temperature_sensor")

        # Update discovered capabilities
        self._discovered_capabilities.update(new_sensors)

        return new_sensors

    async def _analyze_state_transitions(self, product_state: Dict[str, Any]) -> None:
        """Analyze state transitions to understand device behavior patterns."""
        # This could be expanded to learn about device behavior patterns
        # For now, just log interesting state changes

        if isinstance(product_state, dict):
            # Look for state transitions (arrays with [old, new] values)
            transitions = {
                k: v
                for k, v in product_state.items()
                if isinstance(v, list) and len(v) == 2
            }

            if transitions:
                self._logger.debug(
                    "State transitions detected for %s: %s",
                    self.device.serial,
                    transitions,
                )

    async def _enhance_device_capabilities(self, capabilities: Set[str]) -> None:
        """Enhance device with newly discovered capabilities."""
        # This is where we would dynamically add new entities or update existing ones
        # For now, we'll log the enhancement

        self._logger.info(
            "Enhancing device %s with capabilities: %s",
            self.device.serial,
            capabilities,
        )

        # TODO: Implement actual entity enhancement logic
        # This could involve:
        # - Adding new entities to Home Assistant
        # - Updating existing entities with new features
        # - Firing events to notify other components

    async def _enhance_sensor_capabilities(self, sensors: Set[str]) -> None:
        """Enhance device with newly discovered sensor capabilities."""
        self._logger.info(
            "Enhancing device %s with sensors: %s", self.device.serial, sensors
        )

        # TODO: Implement actual sensor enhancement logic

    async def _analyze_current_capabilities(self) -> None:
        """Analyze current device state to establish baseline capabilities."""
        self._logger.debug(
            "Analyzing current capabilities for device %s", self.device.serial
        )

        # If device is already connected and has data, analyze it
        if hasattr(self.device, "state") and self.device.state:
            await self._process_status_data({"product-state": self.device.state})

        if (
            hasattr(self.device, "environmental_state")
            and self.device.environmental_state
        ):
            await self._process_environmental_data(
                {"data": self.device.environmental_state}
            )
