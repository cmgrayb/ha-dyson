"""Config flow for Dyson integration."""

import logging
import threading
from typing import Any, Callable, Optional, cast

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.zeroconf import async_get_instance
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_HOST, CONF_NAME, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError

from .cloud.const import CONF_AUTH, CONF_REGION
from .const import (
    CONF_AUTO_DISCOVERY,
    CONF_CREDENTIAL,
    CONF_DEVICE_TYPE,
    CONF_SERIAL,
    DEFAULT_AUTO_DISCOVERY,
    DOMAIN,
)
from .vendor.libdyson import DEVICE_TYPE_NAMES, get_device, get_mqtt_info_from_wifi_info
from .vendor.libdyson.cloud import (
    REGIONS,
    DysonAccount,
    DysonAccountCN,
    DysonDeviceInfo,
)

# Note: Enhanced device detection now handles device type mapping automatically
from .vendor.libdyson.discovery import DysonDiscovery
from .vendor.libdyson.exceptions import (
    DysonException,
    DysonFailedToParseWifiInfo,
    DysonInvalidAccountStatus,
    DysonInvalidAuth,
    DysonInvalidCredential,
    DysonLoginFailure,
    DysonNetworkError,
    DysonOTPTooFrequently,
)

_LOGGER = logging.getLogger(__name__)

DISCOVERY_TIMEOUT = 10

CONF_METHOD = "method"
CONF_SSID = "ssid"
CONF_MOBILE = "mobile"
CONF_OTP = "otp"

SETUP_METHODS = {
    "wifi": "Setup using your device's Wi-Fi sticker",
    "cloud": "Setup automatically with your MyDyson Account",
    "manual": "Setup manually",
}


# Note: Device type detection is now handled by enhanced MQTT detection
# in device_info.get_mqtt_device_type() instead of manual mapping


class DysonLocalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Dyson local config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return DysonOptionsFlowHandler(config_entry)

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._device_info: Optional[DysonDeviceInfo] = None
        self._reauth_entry: Optional[config_entries.ConfigEntry] = None
        self._email: str = ""
        self._region: str = ""
        self._verify: Optional[Callable[..., Any]] = None

    async def async_step_user(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> ConfigFlowResult:
        """Handle step initialized by user."""
        if user_input is not None:
            if user_input[CONF_METHOD] == "wifi":
                return await self.async_step_wifi()
            if user_input[CONF_METHOD] == "cloud":
                return await self.async_step_cloud()
            return await self.async_step_manual()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_METHOD): vol.In(SETUP_METHODS)}),
        )

    async def async_step_wifi(
        self, info: Optional[dict[str, Any]] = None
    ) -> ConfigFlowResult:
        """Handle step to set up using device Wi-Fi information."""
        errors = {}
        if info is not None:
            try:
                serial, credential, device_type = get_mqtt_info_from_wifi_info(
                    info[CONF_SSID], info[CONF_PASSWORD]
                )
            except DysonFailedToParseWifiInfo:
                errors["base"] = "cannot_parse_wifi_info"
            else:
                device_type_name = DEVICE_TYPE_NAMES[device_type]
                _LOGGER.debug("Successfully parse WiFi information")
                _LOGGER.debug("Serial: %s", serial)
                _LOGGER.debug("Device Type: %s", device_type)
                _LOGGER.debug("Device Type Name: %s", device_type_name)
                try:
                    data = await self._async_get_entry_data(
                        serial,
                        credential,
                        device_type,
                        device_type_name,
                        info.get(CONF_HOST),
                    )
                except InvalidAuth:
                    errors["base"] = "invalid_auth"
                except CannotConnect:
                    errors["base"] = "cannot_connect"
                except CannotFind:
                    errors["base"] = "cannot_find"
                else:
                    return self.async_create_entry(
                        title=device_type_name,
                        data=data,
                    )

        info = info or {}
        return self.async_show_form(
            step_id="wifi",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SSID, default=info.get(CONF_SSID, "")): str,
                    vol.Required(
                        CONF_PASSWORD, default=info.get(CONF_PASSWORD, "")
                    ): str,
                    vol.Optional(CONF_HOST, default=info.get(CONF_HOST, "")): str,
                }
            ),
            errors=errors,
        )

    async def async_step_cloud(
        self, info: Optional[dict[str, Any]] = None
    ) -> ConfigFlowResult:
        if info is not None:
            self._region = info[CONF_REGION]
            if self._region == "CN":
                return await self.async_step_mobile()
            return await self.async_step_email()

        region_names = {code: f"{name} ({code})" for code, name in REGIONS.items()}
        return self.async_show_form(
            step_id="cloud",
            data_schema=vol.Schema({vol.Required(CONF_REGION): vol.In(region_names)}),
        )

    async def async_step_email(
        self, info: Optional[dict[str, Any]] = None
    ) -> ConfigFlowResult:
        errors = {}
        if info is not None:
            email = info[CONF_EMAIL]
            unique_id = f"global_{email}"
            for entry in self._async_current_entries():
                if entry.unique_id == unique_id:
                    return self.async_abort(reason="already_configured")
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            account = DysonAccount()
            try:
                self._verify = await self.hass.async_add_executor_job(
                    account.login_email_otp, email, self._region
                )
            except DysonNetworkError:
                errors["base"] = "cannot_connect_cloud"
            except DysonInvalidAccountStatus:
                errors["base"] = "email_not_registered"
            except DysonInvalidAuth:
                errors["base"] = "invalid_auth"
            else:
                self._email = email
                return await self.async_step_email_otp()

        info = info or {}
        return self.async_show_form(
            step_id="email",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL, default=info.get(CONF_EMAIL, "")): str,
                }
            ),
            errors=errors,
        )

    async def async_step_email_otp(
        self, info: Optional[dict[str, Any]] = None
    ) -> ConfigFlowResult:
        errors = {}
        if info is not None:
            try:
                auth_info = await self.hass.async_add_executor_job(
                    self._verify, info[CONF_OTP], info[CONF_PASSWORD]  # type: ignore[misc]
                )
            except DysonLoginFailure:
                errors["base"] = "invalid_auth"
            else:
                return self.async_create_entry(
                    title=f"MyDyson: {self._email} ({self._region})",
                    data={
                        CONF_REGION: self._region,
                        CONF_AUTH: auth_info,
                    },
                    options={
                        CONF_AUTO_DISCOVERY: info.get(
                            CONF_AUTO_DISCOVERY, DEFAULT_AUTO_DISCOVERY
                        ),
                    },
                )

        return self.async_show_form(
            step_id="email_otp",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): str,
                    vol.Required(CONF_OTP): str,
                    vol.Optional(
                        CONF_AUTO_DISCOVERY, default=DEFAULT_AUTO_DISCOVERY
                    ): bool,
                }
            ),
            errors=errors,
        )

    async def async_step_mobile(
        self, info: Optional[dict[str, Any]] = None
    ) -> ConfigFlowResult:
        errors = {}
        if info is not None:
            account = DysonAccountCN()
            mobile = info[CONF_MOBILE]
            if not mobile.startswith("+"):
                mobile = f"+86{mobile}"
            try:
                self._verify = await self.hass.async_add_executor_job(
                    account.login_mobile_otp, mobile
                )
            except DysonOTPTooFrequently:
                errors["base"] = "otp_too_frequent"
            else:
                self._mobile = mobile
                return await self.async_step_mobile_otp()

        info = info or {}
        return self.async_show_form(
            step_id="mobile",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MOBILE, default=info.get(CONF_MOBILE, "")): str,
                }
            ),
            errors=errors,
        )

    async def async_step_mobile_otp(
        self, info: Optional[dict[str, Any]] = None
    ) -> ConfigFlowResult:
        errors = {}
        if info is not None:
            try:
                auth_info = await self.hass.async_add_executor_job(
                    self._verify, info[CONF_OTP]  # type: ignore[misc]
                )
            except DysonLoginFailure:
                errors["base"] = "invalid_otp"
            else:
                return self.async_create_entry(
                    title=f"MyDyson: {self._mobile} ({self._region})",
                    data={
                        CONF_REGION: self._region,
                        CONF_AUTH: auth_info,
                    },
                    options={
                        CONF_AUTO_DISCOVERY: info.get(
                            CONF_AUTO_DISCOVERY, DEFAULT_AUTO_DISCOVERY
                        ),
                    },
                )

        return self.async_show_form(
            step_id="mobile_otp",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_OTP): str,
                    vol.Optional(
                        CONF_AUTO_DISCOVERY, default=DEFAULT_AUTO_DISCOVERY
                    ): bool,
                }
            ),
            errors=errors,
        )

    async def async_step_manual(
        self, info: Optional[dict[str, Any]] = None
    ) -> ConfigFlowResult:
        """Handle step to setup manually."""
        errors = {}
        if info is not None:
            serial = info[CONF_SERIAL]
            for entry in self._async_current_entries():
                if entry.unique_id == serial:
                    return self.async_abort(reason="already_configured")
            await self.async_set_unique_id(serial)
            self._abort_if_unique_id_configured()

            device_type = info[CONF_DEVICE_TYPE]
            device_type_name = DEVICE_TYPE_NAMES[device_type]
            try:
                data = await self._async_get_entry_data(
                    serial,
                    info[CONF_CREDENTIAL],
                    device_type,
                    device_type_name,
                    info.get(CONF_HOST),
                )
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except CannotFind:
                errors["base"] = "cannot_find"
            else:
                return self.async_create_entry(
                    title=device_type_name,
                    data=data,
                )

        info = info or {}
        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SERIAL, default=info.get(CONF_SERIAL, "")): str,
                    vol.Required(
                        CONF_CREDENTIAL, default=info.get(CONF_CREDENTIAL, "")
                    ): str,
                    vol.Required(
                        CONF_DEVICE_TYPE, default=info.get(CONF_DEVICE_TYPE, "")
                    ): vol.In(DEVICE_TYPE_NAMES),
                    vol.Optional(CONF_HOST, default=info.get(CONF_HOST, "")): str,
                }
            ),
            errors=errors,
        )

    async def async_step_host(
        self, info: Optional[dict[str, Any]] = None
    ) -> ConfigFlowResult:
        """Handle step to set host."""
        errors = {}
        if info is not None:
            assert self._device_info is not None  # Should be set by discovery step
            # Use the enhanced MQTT device type detection which handles all variants properly
            device_type = self._device_info.get_mqtt_device_type()

            _LOGGER.debug(
                "Cloud ProductType: %s, Enhanced MQTT device type: %s, Debug info: %s",
                self._device_info.product_type,
                device_type,
                self._device_info.debug_info(),
            )
            _LOGGER.debug(
                "Device info object has variant attribute: %s",
                hasattr(self._device_info, "variant"),
            )
            if hasattr(self._device_info, "variant"):
                _LOGGER.debug("Raw variant value: %r", self._device_info.variant)
            if device_type is None:
                _LOGGER.error(
                    "Unknown device type for ProductType: %s, variant: %s",
                    self._device_info.product_type,
                    getattr(self._device_info, "variant", None),
                )
                errors["base"] = "unknown_device_type"
            else:
                try:
                    name = info.get(CONF_NAME)
                    if name is None:
                        name = self._device_info.name or self._device_info.serial
                    data = await self._async_get_entry_data(
                        self._device_info.serial,
                        self._device_info.credential,
                        device_type,
                        name,
                        info.get(CONF_HOST),
                    )
                except CannotConnect:
                    errors["base"] = "cannot_connect"
                except CannotFind:
                    errors["base"] = "cannot_find"
                else:
                    title = info.get(CONF_NAME)
                    if title is None:
                        title = self._device_info.name or self._device_info.serial
                    return self.async_create_entry(
                        title=title,
                        data=data,
                    )

        # NOTE: Sometimes, the device is not named. In these situations,
        # default to using the unique serial number as the name.
        assert self._device_info is not None  # Should be set by discovery step
        name = self._device_info.name or self._device_info.serial

        info = info or {}
        return self.async_show_form(
            step_id="host",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_HOST, default=info.get(CONF_HOST, "")): str,
                    vol.Optional(CONF_NAME, default=info.get(CONF_NAME, name)): str,
                }
            ),
            errors=errors,
        )

    async def async_step_discovery(self, discovery_info):
        """Handle step initialized by MyDyson discovery."""
        # discovery_info should be a DysonDeviceInfo object
        info = cast(DysonDeviceInfo, discovery_info)  # Type assertion
        _LOGGER.debug(
            "Starting discovery step for device: %s (ProductType: %s)",
            info.name,
            info.product_type,
        )

        for entry in self._async_current_entries():
            if entry.unique_id == info.serial:
                _LOGGER.debug("Device %s already configured, aborting", info.serial)
                return self.async_abort(reason="already_configured")

        await self.async_set_unique_id(info.serial)
        self._abort_if_unique_id_configured()
        self.context["title_placeholders"] = {
            CONF_NAME: info.name,
            CONF_SERIAL: info.serial,
        }
        self._device_info = info
        _LOGGER.debug(
            "Device %s passed initial checks, proceeding to host step", info.serial
        )
        return await self.async_step_host()

    async def _async_get_entry_data(
        self,
        serial: str,
        credential: str,
        device_type: str,
        name: str,
        host: Optional[str] = None,
    ) -> dict[str, Optional[str]]:
        """Try connect and return config entry data."""
        await self._async_try_connect(serial, credential, device_type, host)
        return {
            CONF_SERIAL: serial,
            CONF_CREDENTIAL: credential,
            CONF_DEVICE_TYPE: device_type,
            CONF_NAME: name,
            CONF_HOST: host,
        }

    async def _async_try_connect(
        self,
        serial: str,
        credential: str,
        device_type: str,
        host: Optional[str] = None,
    ) -> None:
        """Try connect."""
        _LOGGER.debug(
            "Attempting to connect to device: serial=%s, device_type=%s, host=%s",
            serial,
            device_type,
            host,
        )

        device = get_device(serial, credential, device_type)

        # Check if device creation failed
        if device is None:
            _LOGGER.error(
                "Failed to create device object for serial=%s, device_type=%s. "
                "This usually indicates an unknown or unsupported device type.",
                serial,
                device_type,
            )
            raise CannotConnect

        _LOGGER.debug(
            "Successfully created device object of type: %s", type(device).__name__
        )

        # Find device using discovery
        if not host:
            _LOGGER.debug(
                "No host provided, starting device discovery for serial: %s", serial
            )
            discovered = threading.Event()

            def _callback(address: str) -> None:
                _LOGGER.debug("Found device at %s", address)
                nonlocal host
                host = address
                discovered.set()

            discovery = DysonDiscovery()
            discovery.register_device(device, _callback)

            # Log the expected service type for debugging
            expected_service_type = (
                "_360eye_mqtt._tcp.local."
                if device_type == "N223"
                else "_dyson_mqtt._tcp.local."
            )
            _LOGGER.debug(
                "Starting discovery for device_type=%s, expecting service type: %s",
                device_type,
                expected_service_type,
            )

            discovery.start_discovery(await async_get_instance(self.hass))
            succeed = await self.hass.async_add_executor_job(
                discovered.wait, DISCOVERY_TIMEOUT
            )
            discovery.stop_discovery()
            if not succeed:
                _LOGGER.error(
                    "Discovery timed out for device serial=%s, device_type=%s. "
                    "Expected service type: %s",
                    serial,
                    device_type,
                    expected_service_type,
                )
                raise CannotFind

            _LOGGER.debug("Discovery successful, device found at: %s", host)

        # Try connect to the device
        _LOGGER.debug("Attempting MQTT connection to device at %s", host)
        try:
            if host is not None:
                device.connect(host)
                _LOGGER.debug("Successfully connected to device via MQTT")
            else:
                _LOGGER.error("No host available for connection")
                raise CannotConnect
        except DysonInvalidCredential:
            _LOGGER.error("Invalid credentials for device serial=%s", serial)
            raise InvalidAuth
        except DysonException as err:
            _LOGGER.error(
                "Failed to connect to device serial=%s, device_type=%s, host=%s: %s (%s)",
                serial,
                device_type,
                host,
                type(err).__name__,
                err,
            )

            # Add specific logging for MQTT connection refused errors
            if "Connection refused" in str(err) or "result code 7" in str(err):
                _LOGGER.error(
                    "MQTT connection refused (result code 7) - this may indicate:"
                )
                _LOGGER.error(
                    "  1. Wrong device type mapping (expected: %s)", device_type
                )
                _LOGGER.error("  2. Device firmware issue or unexpected state")
                _LOGGER.error("  3. MQTT broker unavailable on device")
                _LOGGER.error("  4. Network connectivity problems")
                _LOGGER.error("  5. Device already has too many connections")

            raise CannotConnect

    async def async_step_reauth(self, data: Optional[dict] = None):
        """Handle reauthentication flow when cloud credentials are invalid."""
        entry_id = self.context.get("entry_id")
        if not entry_id:
            _LOGGER.error("No entry_id found in reauth context")
            return self.async_abort(reason="reauth_failed")

        _LOGGER.debug("Starting reauthentication flow for entry: %s", entry_id)

        # Store the entry_id for later use
        self._reauth_entry = self.hass.config_entries.async_get_entry(entry_id)

        if self._reauth_entry is None:
            _LOGGER.error("Could not find config entry for reauthentication")
            return self.async_abort(reason="reauth_failed")

        # Check if this was a cloud-based setup that needs reauthentication
        if CONF_AUTH in self._reauth_entry.data:
            return await self.async_step_reauth_cloud()
        else:
            # For local-only setups, there's no cloud auth to refresh
            _LOGGER.warning("Reauth requested for local-only setup - nothing to do")
            return self.async_abort(reason="reauth_not_needed")

    async def async_step_reauth_cloud(self, user_input: Optional[dict] = None):
        """Handle cloud reauthentication - collect email and start OTP flow."""
        errors = {}

        if user_input is not None:
            try:
                # Store email and region for OTP verification
                self._email = user_input[CONF_EMAIL]
                self._region = self._reauth_entry.data.get(CONF_REGION, "US")  # type: ignore[union-attr]

                if self._region == "CN":
                    account = DysonAccountCN()
                else:
                    account = DysonAccount()

                # Start OTP flow
                self._verify = await self.hass.async_add_executor_job(
                    account.login_email_otp, self._email, self._region
                )

                return await self.async_step_reauth_otp()

            except DysonInvalidAuth:
                errors["base"] = "invalid_auth"
            except DysonNetworkError:
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.error("Unexpected error during reauthentication setup: %s", err)
                errors["base"] = "unknown"

        # Show the form to enter email
        return self.async_show_form(
            step_id="reauth_cloud",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL, default=""): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "name": self._reauth_entry.data.get(CONF_NAME, "Dyson Device") if self._reauth_entry else "Dyson Device",  # type: ignore[union-attr]
            },
        )

    async def async_step_reauth_otp(self, user_input: Optional[dict] = None):
        """Handle OTP verification for reauthentication."""
        errors = {}

        if user_input is not None:
            try:
                # Verify OTP and get new auth info
                auth_info = await self.hass.async_add_executor_job(
                    self._verify, user_input[CONF_OTP], user_input[CONF_PASSWORD]  # type: ignore[misc]
                )

                # Update the config entry with new auth info
                if self._reauth_entry:
                    new_data = {**self._reauth_entry.data}
                    new_data[CONF_AUTH] = auth_info

                    self.hass.config_entries.async_update_entry(
                        self._reauth_entry,
                        data=new_data,
                    )

                    _LOGGER.info(
                        "Successfully updated cloud credentials for entry: %s",
                        self._reauth_entry.entry_id,
                    )
                    return self.async_abort(reason="reauth_successful")
                else:
                    return self.async_abort(reason="reauth_failed")

            except DysonLoginFailure:
                errors["base"] = "invalid_auth"
            except DysonInvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception as err:
                _LOGGER.error("Unexpected error during OTP verification: %s", err)
                errors["base"] = "unknown"

        # Show OTP form
        return self.async_show_form(
            step_id="reauth_otp",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_OTP): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "email": self._email,
            },
        )


class DysonOptionsFlowHandler(config_entries.OptionsFlow):
    """Dyson options flow handler."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Check if this is a cloud-configured device
        if CONF_AUTH in self.config_entry.data:
            # Cloud device - show full options with interval description
            from .const import (
                CONF_CLOUD_POLL_INTERVAL,
                CONF_ENABLE_POLLING,
                DEFAULT_CLOUD_POLL_INTERVAL,
                DEFAULT_ENABLE_POLLING,
            )

            current_interval = self.config_entry.options.get(
                CONF_CLOUD_POLL_INTERVAL, DEFAULT_CLOUD_POLL_INTERVAL
            )
            current_auto_discovery = self.config_entry.options.get(
                CONF_AUTO_DISCOVERY, DEFAULT_AUTO_DISCOVERY
            )
            current_enable_polling = self.config_entry.options.get(
                CONF_ENABLE_POLLING, DEFAULT_ENABLE_POLLING
            )

            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            CONF_AUTO_DISCOVERY, default=current_auto_discovery
                        ): bool,
                        vol.Optional(
                            CONF_ENABLE_POLLING, default=current_enable_polling
                        ): bool,
                        vol.Optional(
                            CONF_CLOUD_POLL_INTERVAL, default=current_interval
                        ): vol.All(
                            vol.Coerce(int), vol.Range(min=300, max=86400)
                        ),  # 5 min to 24 hours
                    }
                ),
                description_placeholders={
                    "current_interval": str(current_interval // 60),  # Show in minutes
                },
            )
        else:
            # Local device - use separate step without interval variable
            return await self.async_step_local_options(user_input)

    async def async_step_local_options(self, user_input=None):
        """Manage local device options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        from .const import CONF_ENABLE_POLLING, DEFAULT_ENABLE_POLLING

        current_enable_polling = self.config_entry.options.get(
            CONF_ENABLE_POLLING, DEFAULT_ENABLE_POLLING
        )

        return self.async_show_form(
            step_id="local_options",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_ENABLE_POLLING, default=current_enable_polling
                    ): bool,
                }
            ),
        )


class CannotConnect(HomeAssistantError):
    """Represents connection failure."""


class CannotFind(HomeAssistantError):
    """Represents discovery failure."""


class InvalidAuth(HomeAssistantError):
    """Represents invalid authentication."""
