"""Constants for Dyson Local."""

DOMAIN = "dyson_local"

CONF_SERIAL = "serial"
CONF_CREDENTIAL = "credential"
CONF_DEVICE_TYPE = "device_type"
CONF_CLOUD_POLL_INTERVAL = "cloud_poll_interval"
CONF_AUTO_DISCOVERY = "auto_discovery"
CONF_ENABLE_POLLING = "enable_polling"
CONF_PROGRESSIVE_DISCOVERY = "progressive_discovery"

DATA_DEVICES = "devices"
DATA_DISCOVERY = "discovery"
DATA_COORDINATORS = "coordinators"

# Default poll intervals
DEFAULT_CLOUD_POLL_INTERVAL = 3600  # 1 hour in seconds
DEFAULT_AUTO_DISCOVERY = True  # Enable auto-discovery by default
DEFAULT_ENABLE_POLLING = True  # Enable polling for changes by default
DEFAULT_PROGRESSIVE_DISCOVERY = True  # Enable progressive discovery by default

# Device-specific constants
PURE_COOL_LINK_FILTER_LIFE_MAX_HOURS = (
    4300  # Maximum filter life in hours for Pure Cool Link
)
