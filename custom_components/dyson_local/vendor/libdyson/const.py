"""Constants for Dyson Python library - Simplified for MQTT-focused usage."""

from enum import Enum, auto
from typing import Optional

# =============================================================================
# DEVICE TYPE CONSTANTS - MQTT TOPIC FORMATION ONLY
# =============================================================================
# These constants are used ONLY for forming MQTT topics: {device_type}/{serial}/command
# Device classification and capability detection is handled by dynamic discovery

# Vacuum Robots (special cases - always use static mapping)
DEVICE_TYPE_360_EYE = "N223"
DEVICE_TYPE_360_HEURIST = "276"
DEVICE_TYPE_360_VIS_NAV = "277"

# Modern Devices - Base Types (capability discovery handles classification)
DEVICE_TYPE_358 = "358"  # PH Series Pure Humidify+Cool Tower Fans
DEVICE_TYPE_438 = "438"  # TP Series Pure Cool Tower Fans
DEVICE_TYPE_527 = "527"  # HP Series Pure Hot+Cool Tower Fans
DEVICE_TYPE_664 = "664"  # BP Series Purifier Big+Quiet Tower Fans
DEVICE_TYPE_739 = "739"  # AM Series Pure Cool Desktop Tower Fans

# Legacy Devices (limited MQTT data - require static mapping)
DEVICE_TYPE_PURE_COOL_LINK = "475"  # TP02 Pure Cool Link
DEVICE_TYPE_PURE_COOL_LINK_DESK = "469"  # DP01/DP02 Pure Cool Link Desk
DEVICE_TYPE_PURE_HOT_COOL_LINK = "455"  # HP02 Pure Hot+Cool Link
DEVICE_TYPE_PURE_COOL_DESK = "520"  # AM06 Pure Cool Desk


def construct_device_type(base_type: str, variant: Optional[str] = None) -> str:
    """Construct device type string for MQTT topic formation.

    Args:
        base_type: Base device type (e.g., "438", "527", "358")
        variant: Optional regional variant (e.g., "K", "E", "M")

    Returns:
        Device type string for MQTT topics (e.g., "438K", "527E")

    Examples:
        construct_device_type("438", "K") → "438K"
        construct_device_type("527", "E") → "527E"
        construct_device_type("739") → "739"
    """
    if variant:
        return f"{base_type}{variant}"
    return base_type


# =============================================================================
# DEVICE TYPE NAMES - SIMPLIFIED MODEL IDENTIFICATION
# =============================================================================
DEVICE_TYPE_NAMES = {
    # Vacuum Robots
    DEVICE_TYPE_360_EYE: "360 Eye robot vacuum",
    DEVICE_TYPE_360_HEURIST: "360 Heurist robot vacuum",
    DEVICE_TYPE_360_VIS_NAV: "360 Vis Nav robot vacuum",
    # Modern Devices (capabilities discovered dynamically)
    DEVICE_TYPE_739: "AM Series Pure Cool Desktop Tower Fan",
    DEVICE_TYPE_438: "TP Series Pure Cool Tower Fan",
    DEVICE_TYPE_527: "HP Series Pure Hot+Cool Tower Fan",
    DEVICE_TYPE_358: "PH Series Pure Humidify+Cool Tower Fan",
    DEVICE_TYPE_664: "BP Series Purifier Big+Quiet Tower Fan",
    # Legacy Devices (static mapping required)
    DEVICE_TYPE_PURE_COOL_LINK: "TP02 Pure Cool Link",
    DEVICE_TYPE_PURE_COOL_LINK_DESK: "DP01/DP02 Pure Cool Link Desk",
    DEVICE_TYPE_PURE_HOT_COOL_LINK: "HP02 Pure Hot+Cool Link",
    DEVICE_TYPE_PURE_COOL_DESK: "AM06 Pure Cool Desk",
}

# =============================================================================
# BACKWARD COMPATIBILITY ALIASES - ESSENTIAL ONLY
# =============================================================================
# Critical aliases to maintain compatibility with major integrations
# All regional variants (E/K/M) are functionally identical - only MQTT topics differ

# AM12 compatibility
DEVICE_TYPE_PURE_COOL_AM12 = DEVICE_TYPE_739

# TP Series compatibility (all TP models map to base type for capability discovery)
DEVICE_TYPE_PURE_COOL = DEVICE_TYPE_438
# Note: Regional variants like TP07K, TP09E automatically handled by base type

# HP Series compatibility (all HP models map to base type for capability discovery)
DEVICE_TYPE_PURE_HOT_COOL = DEVICE_TYPE_527
# Note: Regional variants like HP07E, HP09K automatically handled by base type

# PH Series compatibility (all PH models map to base type for capability discovery)
DEVICE_TYPE_PURE_HUMIDIFY_COOL = DEVICE_TYPE_358
# Note: Regional variants like PH03K, PH04E automatically handled by base type

# BP Series compatibility
DEVICE_TYPE_PURIFIER_BIG_QUIET = DEVICE_TYPE_664

# =============================================================================
# MQTT TOPIC FAMILIES - DYNAMIC APPROACH
# =============================================================================
# Maps base MQTT topic prefixes to device families
# Use construct_device_type() to build specific device types with variants

MQTT_TOPIC_FAMILIES = {
    "739": ["AM Series", "Tower Fan"],
    "438": ["TP Series", "Pure Cool Purifiers (all regional variants: base, K, E, M)"],
    "527": [
        "HP Series",
        "Pure Hot+Cool Purifiers (all regional variants: base, E, K, M)",
    ],
    "358": [
        "PH Series",
        "Pure Humidify+Cool Purifiers (all regional variants: base, K, E)",
    ],
    "664": ["BP Series", "Purifier Big+Quiet"],
    "475": ["Legacy TP02", "Pure Cool Link"],
    "469": ["Legacy DP01/DP02", "Pure Cool Link Desk"],
    "455": ["Legacy HP02", "Pure Hot+Cool Link"],
    "520": ["Legacy AM06", "Pure Cool Desk"],
    "N223": ["360 Eye", "Robot Vacuum"],
    "276": ["360 Heurist", "Robot Vacuum"],
    "277": ["360 Vis Nav", "Robot Vacuum"],
}

# =============================================================================
# UNCHANGED CONSTANTS
# =============================================================================
# These constants remain unchanged as they're not related to device classification

ENVIRONMENTAL_OFF = -1
ENVIRONMENTAL_INIT = -2
ENVIRONMENTAL_FAIL = -3


class MessageType(Enum):
    """Update message type."""

    STATE = auto()
    ENVIRONMENTAL = auto()


class AirQualityTarget(Enum):
    """Air Quality Target."""

    OFF = "OFF"
    GOOD = "0004"
    SENSITIVE = "0003"
    DEFAULT = "0002"
    VERY_SENSITIVE = "0001"


class HumidifyOscillationMode(Enum):
    """Pure Humidify+Cool oscillation mode."""

    DEGREE_45 = "0045"
    DEGREE_90 = "0090"
    BREEZE = "BRZE"
    CUST = "CUST"


class Tilt(Enum):
    """Pure Humidify+Cool oscillation mode."""

    DEGREE_0 = "0000"
    DEGREE_25 = "0025"
    DEGREE_50 = "0050"
    BREEZE = "0359"


class WaterHardness(Enum):
    """Water Hardness."""

    SOFT = "Soft"
    MEDIUM = "Medium"
    HARD = "Hard"


class VacuumState(Enum):
    """Dyson vacuum state."""

    FAULT_CALL_HELPLINE = "FAULT_CALL_HELPLINE"
    FAULT_CONTACT_HELPLINE = "FAULT_CONTACT_HELPLINE"
    FAULT_CRITICAL = "FAULT_CRITICAL"
    FAULT_GETTING_INFO = "FAULT_GETTING_INFO"
    FAULT_LOST = "FAULT_LOST"
    FAULT_ON_DOCK = "FAULT_ON_DOCK"
    FAULT_ON_DOCK_CHARGED = "FAULT_ON_DOCK_CHARGED"
    FAULT_ON_DOCK_CHARGING = "FAULT_ON_DOCK_CHARGING"
    FAULT_REPLACE_ON_DOCK = "FAULT_REPLACE_ON_DOCK"
    FAULT_RETURN_TO_DOCK = "FAULT_RETURN_TO_DOCK"
    FAULT_RUNNING_DIAGNOSTIC = "FAULT_RUNNING_DIAGNOSTIC"
    FAULT_USER_RECOVERABLE = "FAULT_USER_RECOVERABLE"
    FULL_CLEAN_ABANDONED = "FULL_CLEAN_ABANDONED"
    FULL_CLEAN_ABORTED = "FULL_CLEAN_ABORTED"
    FULL_CLEAN_CHARGING = "FULL_CLEAN_CHARGING"
    FULL_CLEAN_DISCOVERING = "FULL_CLEAN_DISCOVERING"
    FULL_CLEAN_FINISHED = "FULL_CLEAN_FINISHED"
    FULL_CLEAN_INITIATED = "FULL_CLEAN_INITIATED"
    FULL_CLEAN_NEEDS_CHARGE = "FULL_CLEAN_NEEDS_CHARGE"
    FULL_CLEAN_PAUSED = "FULL_CLEAN_PAUSED"
    FULL_CLEAN_RUNNING = "FULL_CLEAN_RUNNING"
    FULL_CLEAN_TRAVERSING = "FULL_CLEAN_TRAVERSING"
    INACTIVE_CHARGED = "INACTIVE_CHARGED"
    INACTIVE_CHARGING = "INACTIVE_CHARGING"
    INACTIVE_DISCHARGING = "INACTIVE_DISCHARGING"
    MAPPING_ABORTED = "MAPPING_ABORTED"
    MAPPING_CHARGING = "MAPPING_CHARGING"
    MAPPING_FINISHED = "MAPPING_FINISHED"
    MAPPING_INITIATED = "MAPPING_INITIATED"
    MAPPING_NEEDS_CHARGE = "MAPPING_NEEDS_CHARGE"
    MAPPING_PAUSED = "MAPPING_PAUSED"
    MAPPING_RUNNING = "MAPPING_RUNNING"


class VacuumEyePowerMode(Enum):
    """Dyson 360 Eye power mode."""

    QUIET = "halfPower"
    MAX = "fullPower"


class VacuumHeuristPowerMode(Enum):
    """Dyson 360 Heurist power mode."""

    QUIET = "1"
    HIGH = "2"
    MAX = "3"


class VacuumVisNavPowerMode(Enum):
    """Dyson 360 Heurist power mode."""

    AUTO = "1"
    QUICK = "2"
    QUIET = "3"
    BOOST = "4"


class CleaningType(Enum):
    """Vacuum cleaning type."""

    IMMEDIATE = "immediate"
    MANUAL = "manual"
    SCHEDULED = "scheduled"


class CleaningMode(Enum):
    """Vacuum cleaning mode."""

    GLOBAL = "global"
    ZONE_CONFIGURED = "zoneConfigured"
