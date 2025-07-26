"""Constants for Dyson Local."""

DOMAIN = "dyson_local"

CONF_SERIAL = "serial"
CONF_CREDENTIAL = "credential"
CONF_DEVICE_TYPE = "device_type"
CONF_CLOUD_POLL_INTERVAL = "cloud_poll_interval"
CONF_AUTO_DISCOVERY = "auto_discovery"
CONF_ENABLE_POLLING = "enable_polling"

DATA_DEVICES = "devices"
DATA_DISCOVERY = "discovery"
DATA_COORDINATORS = "coordinators"

# Default poll intervals
DEFAULT_CLOUD_POLL_INTERVAL = 3600  # 1 hour in seconds
DEFAULT_AUTO_DISCOVERY = True  # Enable auto-discovery by default
DEFAULT_ENABLE_POLLING = True  # Enable polling for changes by default
