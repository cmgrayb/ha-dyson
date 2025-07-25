"""Cloud account management for Dyson integration."""

import logging

from homeassistant import config_entries
from homeassistant.config_entries import SOURCE_DISCOVERY, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

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
        raise ConfigEntryAuthFailed(
            "Authentication failed - please reconfigure with valid credentials"
        )
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


async def async_handle_auth_failure(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle authentication failure during runtime operations."""
    _LOGGER.warning(
        "Authentication failed for Dyson cloud account. Initiating reauth flow for entry: %s",
        entry.entry_id,
    )

    # Trigger the reauth flow
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": entry.entry_id,
            },
            data=entry.data,
        )
    )


async def async_check_auth_and_refresh_devices(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Check authentication and refresh device list, handling auth failures gracefully."""
    _LOGGER.debug(
        "Checking cloud authentication and refreshing devices for entry: %s",
        entry.entry_id,
    )

    if entry.entry_id not in hass.data[DOMAIN]:
        _LOGGER.warning("Entry data not found for %s", entry.entry_id)
        return False

    account_data = hass.data[DOMAIN][entry.entry_id].get(DATA_ACCOUNT)
    if not account_data:
        _LOGGER.warning("Account data not found for %s", entry.entry_id)
        return False

    try:
        # Attempt to refresh device list to verify credentials are still valid
        devices = await hass.async_add_executor_job(account_data.devices)
        _LOGGER.debug(
            "Successfully verified cloud credentials and retrieved %d devices",
            len(devices),
        )

        # Update the stored devices list
        hass.data[DOMAIN][entry.entry_id][DATA_DEVICES] = devices
        return True

    except DysonInvalidAuth:
        _LOGGER.error("Cloud authentication failed - credentials may have been changed")
        await async_handle_auth_failure(hass, entry)
        return False

    except DysonNetworkError:
        _LOGGER.warning("Network error checking cloud credentials - will retry later")
        return False

    except Exception as e:
        _LOGGER.error("Unexpected error checking cloud credentials: %s", str(e))
        return False
