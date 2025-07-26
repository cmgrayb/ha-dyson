"""Cloud account management for Dyson integration."""

import logging

from homeassistant.config_entries import SOURCE_DISCOVERY, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from ..cloud.const import CONF_AUTH, CONF_REGION, DATA_ACCOUNT, DATA_DEVICES
from ..const import DOMAIN
from ..vendor.libdyson.cloud import DysonAccount, DysonAccountCN
from ..vendor.libdyson.exceptions import DysonInvalidAuth, DysonNetworkError

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["camera"]


async def async_setup_account(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a MyDyson Account."""
    _LOGGER.debug("Setting up MyDyson Account for region: %s", entry.data[CONF_REGION])

    if entry.data[CONF_REGION] == "CN":
        account = DysonAccountCN(entry.data[CONF_AUTH])
    else:
        account = DysonAccount(entry.data[CONF_AUTH])

    try:
        _LOGGER.debug("Calling account.devices() to get device list")
        devices = await hass.async_add_executor_job(account.devices)
        _LOGGER.debug("Retrieved %d devices from cloud", len(devices))
    except DysonNetworkError:
        _LOGGER.error("Cannot connect to Dyson cloud service.")
        raise ConfigEntryNotReady
    except DysonInvalidAuth:
        _LOGGER.error("Invalid authentication credentials for Dyson cloud service.")
        raise ConfigEntryNotReady
    except Exception as e:
        _LOGGER.error("Unexpected error retrieving devices: %s", str(e))
        raise ConfigEntryNotReady

    _LOGGER.debug("Starting device discovery flows for %d devices", len(devices))
    for device in devices:
        _LOGGER.debug(
            "Creating discovery flow for device: %s (ProductType: %s)",
            device.name,
            device.product_type,
        )
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_DISCOVERY},
                data=device,
            )
        )

    hass.data[DOMAIN][entry.entry_id] = {
        DATA_ACCOUNT: account,
        DATA_DEVICES: devices,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
