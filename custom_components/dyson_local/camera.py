"""Camera platform for Dyson cloud."""

from datetime import timedelta
import logging
from typing import Callable

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .cloud.const import DATA_ACCOUNT, DATA_DEVICES
from .const import DOMAIN
from .vendor.libdyson.cloud import DysonDeviceInfo
from .vendor.libdyson.cloud.cloud_360_eye import DysonCloud360Eye
from .vendor.libdyson.const import DEVICE_TYPE_360_EYE

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=30)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Callable
) -> None:
    """Set up Dyson fan from a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    account = data[DATA_ACCOUNT]
    devices = data[DATA_DEVICES]
    entities = []
    for device in devices:
        if device.product_type not in [DEVICE_TYPE_360_EYE]:
            continue
        entities.append(
            DysonCleaningMapEntity(
                DysonCloud360Eye(account, device.serial),
                device,
            )
        )
    async_add_entities(entities, True)


class DysonCleaningMapEntity(Camera):
    """Dyson vacuum cleaning map entity."""

    def __init__(self, device: DysonCloud360Eye, device_info: DysonDeviceInfo):
        super().__init__()
        self._device = device
        self._device_info = device_info
        self._last_cleaning_task = None
        self._image = None

        # Set attributes instead of properties to avoid override issues
        self._attr_name = f"{self._device_info.name} Cleaning Map"
        self._attr_unique_id = self._device_info.serial
        self._attr_icon = "mdi:map"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._device_info.serial)},
            "name": self._device_info.name,
            "manufacturer": "Dyson",
            "model": self._device_info.product_type,
            "sw_version": self._device_info.version,
        }

    def camera_image(self, width=None, height=None):
        """Return cleaning map. Width and height are ignored."""
        return self._image

    def update(self):
        """Check for map update."""
        _LOGGER.debug("Running cleaning map update for %s", self._device_info.name)
        cleaning_tasks = self._device.get_cleaning_history()

        last_task = None
        for task in cleaning_tasks:
            if task.area > 0.0:
                # Skip cleaning tasks with 0 area, map not available
                last_task = task
                break
        if last_task is None:
            _LOGGER.debug("No cleaning history found.")
            self._last_cleaning_task = None
            return

        if last_task == self._last_cleaning_task:
            _LOGGER.debug("Cleaning task not changed. Skip update.")
            return
        self._last_cleaning_task = last_task
        self._image = self._device.get_cleaning_map(
            self._last_cleaning_task.cleaning_id
        )
