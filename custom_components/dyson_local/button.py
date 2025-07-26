import logging
from typing import Callable, Optional

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory  # type: ignore[attr-defined]

from .const import DATA_DEVICES, DOMAIN
from .entity import DysonEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Callable[..., None],
) -> None:
    """Set up Dyson button from a config entry."""
    device = hass.data[DOMAIN][DATA_DEVICES][config_entry.entry_id]
    name = config_entry.data[CONF_NAME]

    entities = []

    if hasattr(device, "filter_life"):
        entities.append(DysonFilterResetButton(device, name))

    async_add_entities(entities)


class DysonButton(ButtonEntity, DysonEntity):
    """Base class for Dyson button entities."""

    _attr_entity_category = EntityCategory.CONFIG


class DysonFilterResetButton(DysonButton):
    """Button to reset filter life on Dyson devices."""

    @property
    def sub_name(self) -> Optional[str]:
        """Return the name of the Dyson button."""
        return "Reset Filter Life"

    @property
    def sub_unique_id(self) -> str:
        """Return the button's unique id."""
        return "reset-filter"

    def press(self) -> None:
        """Press the button to reset filter life."""
        self._device.reset_filter()  # type: ignore[attr-defined]
