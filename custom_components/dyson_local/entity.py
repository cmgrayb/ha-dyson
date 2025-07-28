"""Base entity for Dyson devices."""

import logging
import time
from typing import Any, Optional

from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .vendor.libdyson import MessageType
from .vendor.libdyson.dyson_device import DysonDevice

_LOGGER = logging.getLogger(__name__)

# Global tracking for oscillation updates to prevent infinite loops
_oscillation_update_locks: dict[str, bool] = {}
_oscillation_update_timestamps: dict[str, float] = {}


class DysonEntity(Entity):
    """Dyson entity base class."""

    _MESSAGE_TYPE = MessageType.STATE

    def __init__(self, device: DysonDevice, name: str):
        """Initialize the entity."""
        self._device = device
        self._name = name
        self._last_oscillation_state: Optional[dict[str, Any]] = (
            None  # Track the last known oscillation state
        )

        # Set attributes to avoid property override issues
        self._attr_should_poll = False

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to hass."""
        self._device.add_message_listener(self._on_message)

    async def async_will_remove_from_hass(self) -> None:
        """Call when entity will be removed from hass."""
        try:
            self._device.remove_message_listener(self._on_message)
        except Exception as e:
            _LOGGER.debug(
                "Error removing message listener for %s: %s", self.unique_id, e
            )

    def _on_message(self, message_type: MessageType) -> None:
        if self._MESSAGE_TYPE is None or message_type == self._MESSAGE_TYPE:
            self.schedule_update_ha_state()

    def _is_oscillation_entity(self) -> bool:
        """Check if this is an oscillation-related entity."""
        # Only consider entities that are specifically oscillation-related
        # Don't include all entities from devices that support oscillation
        return (
            hasattr(self, "sub_unique_id")
            and bool(self.sub_unique_id)
            and (
                "oscillation" in str(self.sub_unique_id)
                or "angle" in str(self.sub_unique_id)
            )
        )

    def _schedule_oscillation_entities_update_debounced(self) -> None:
        """Schedule state updates for oscillation-related entities with debouncing."""
        device_serial = self._device.serial
        current_time = time.time()

        # Check if we've updated recently (within 0.5 seconds) to prevent loops
        if (
            device_serial in _oscillation_update_timestamps
            and current_time - _oscillation_update_timestamps[device_serial] < 0.5
        ):
            _LOGGER.debug(
                "Skipping oscillation sync for %s - recent update", device_serial
            )
            return

        # Update timestamp
        _oscillation_update_timestamps[device_serial] = current_time

        # Schedule the actual update
        self._schedule_oscillation_entities_update()

    def _schedule_oscillation_entities_update(self) -> None:
        """Schedule state updates for oscillation-related entities."""
        _LOGGER.debug(
            "Scheduling oscillation entities update for device %s", self._device.serial
        )

        # This will be called from entity classes when oscillation settings change
        # The message listener mechanism should handle the updates automatically
        # Don't force additional status requests as they may interfere with normal data flow

        # Also trigger direct entity updates
        self._trigger_oscillation_entities_update()

    def _trigger_oscillation_entities_update(self) -> None:
        """Trigger updates for all oscillation-related entities."""
        _LOGGER.debug(
            "Triggering oscillation entities update for device %s", self._device.serial
        )

        # Schedule updates for all entities through the device's message system
        # This ensures that all entities get the latest state from the device
        if hasattr(self._device, "_callbacks"):
            updated_count = 0
            for callback in self._device._callbacks:
                # Check if the callback is from a DysonEntity (has _is_oscillation_entity method)
                if hasattr(callback, "__self__") and hasattr(
                    callback.__self__, "_is_oscillation_entity"
                ):
                    entity = callback.__self__
                    if entity._is_oscillation_entity():
                        try:
                            entity.schedule_update_ha_state(force_refresh=True)
                            updated_count += 1
                            _LOGGER.debug(
                                "Triggered update for oscillation entity: %s",
                                getattr(entity, "entity_id", "unknown"),
                            )
                        except Exception as e:
                            _LOGGER.debug("Error triggering update for entity: %s", e)

            _LOGGER.debug(
                "Triggered updates for %d oscillation entities for device %s",
                updated_count,
                self._device.serial,
            )
        else:
            _LOGGER.debug("Device %s has no _callbacks attribute", self._device.serial)

    def schedule_update_ha_state(self, force_refresh: bool = False) -> None:
        """Schedule an update for this entity."""
        # Call the parent method
        super().schedule_update_ha_state(force_refresh)

    def _check_oscillation_state_change(self) -> None:
        """Check if oscillation state changed and trigger sync if needed."""
        try:
            current_state = self._get_current_oscillation_state()

            if (
                self._last_oscillation_state is not None
                and current_state != self._last_oscillation_state
            ):
                _LOGGER.debug(
                    "Oscillation state change detected in %s: %s -> %s",
                    self.unique_id,
                    self._last_oscillation_state,
                    current_state,
                )
                # State changed - trigger sync for all related entities
                self._schedule_oscillation_entities_update_debounced()

            self._last_oscillation_state = current_state
        except Exception as e:
            _LOGGER.debug(
                "Error checking oscillation state change in %s: %s", self.unique_id, e
            )

    def _get_current_oscillation_state(self) -> dict[str, Any]:
        """Get the current oscillation state for comparison."""
        # Return relevant oscillation state that should trigger sync when changed
        if hasattr(self._device, "oscillation_angle_low"):
            return {
                "oscillation": getattr(self._device, "oscillation", None),
                "angle_low": getattr(self._device, "oscillation_angle_low", None),
                "angle_high": getattr(self._device, "oscillation_angle_high", None),
                "center": getattr(self._device, "oscillation_center", None),
            }
        return {}

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        if self.sub_name is None:
            return self._name
        return f"{self._name} {self.sub_name}"

    @property
    def sub_name(self) -> Optional[str]:
        """Return sub name of the entity."""
        return None

    @property
    def unique_id(self) -> str:
        """Return the entity unique id."""
        if self.sub_unique_id is None:
            return self._device.serial
        return f"{self._device.serial}-{self.sub_unique_id}"

    @property
    def sub_unique_id(self) -> Optional[str]:
        """Return the entity sub unique id."""
        return None

    @property
    def device_info(self) -> dict[str, Any]:  # type: ignore[override]
        """Return device info of the entity."""
        return {
            "identifiers": {(DOMAIN, self._device.serial)},
            "name": self._name,
            "manufacturer": "Dyson",
            "model": self._device.device_type,
        }
