"""Constants for Dyson Python library."""
from enum import Enum, auto

DEVICE_TYPE_360_EYE = "N223"
DEVICE_TYPE_360_HEURIST = "276"
DEVICE_TYPE_360_VIS_NAV = "277"
DEVICE_TYPE_PURE_COOL_LINK_DESK = "469"  # DP01? DP02? This one's a bit older, and scraping the Dyson website is unclear
DEVICE_TYPE_PURE_COOL_DESK = "520"  # AM06? This one's also a bit older, and also hard to scrape off the Dyson website
DEVICE_TYPE_PURE_COOL_LINK = "475"  # TP02
DEVICE_TYPE_PURE_COOL = "438"  # TP04, TP07, TP09, TP11, PC1 - all variants merged, use same DysonPureCool class
DEVICE_TYPE_PURIFIER_COOL_K = "438K"  # Deprecated: use DEVICE_TYPE_PURE_COOL instead (kept for MQTT topic compatibility)
DEVICE_TYPE_PURIFIER_COOL_E = "438E"  # Deprecated: use DEVICE_TYPE_PURE_COOL instead (kept for MQTT topic compatibility)
DEVICE_TYPE_PURIFIER_COOL_M = "438M"  # Deprecated: use DEVICE_TYPE_PURE_COOL instead (kept for MQTT topic compatibility)
DEVICE_TYPE_PURE_HUMIDIFY_COOL = "358"  # PH01, PH02, PH03, PH04 - all variants merged, use same DysonPurifierHumidifyCool class
DEVICE_TYPE_PURIFIER_HUMIDIFY_COOL_K = "358K"  # Deprecated: use DEVICE_TYPE_PURE_HUMIDIFY_COOL instead (kept for MQTT topic compatibility)
DEVICE_TYPE_PURIFIER_HUMIDIFY_COOL_E = "358E"  # Deprecated: use DEVICE_TYPE_PURE_HUMIDIFY_COOL instead (kept for MQTT topic compatibility)
DEVICE_TYPE_PURE_HOT_COOL_LINK = "455"  # HP02
DEVICE_TYPE_PURE_HOT_COOL = "527"  # HP04, HP07, HP09 - all variants merged, use same DysonPureHotCool class
DEVICE_TYPE_PURIFIER_HOT_COOL_E = "527E"  # Deprecated: use DEVICE_TYPE_PURE_HOT_COOL instead (kept for MQTT topic compatibility)
DEVICE_TYPE_PURIFIER_HOT_COOL_K = "527K"  # Deprecated: use DEVICE_TYPE_PURE_HOT_COOL instead (kept for MQTT topic compatibility)
DEVICE_TYPE_PURIFIER_HOT_COOL_M = "527M"  # Deprecated: use DEVICE_TYPE_PURE_HOT_COOL instead (kept for MQTT topic compatibility)
DEVICE_TYPE_PURIFIER_BIG_QUIET = "664"  # BP02, BP03, and BP04

DEVICE_TYPE_NAMES = {
    DEVICE_TYPE_360_EYE: "360 Eye robot vacuum",
    DEVICE_TYPE_360_HEURIST: "360 Heurist robot vacuum",
    DEVICE_TYPE_360_VIS_NAV: "360 Vis Nav robot vacuum",
    DEVICE_TYPE_PURE_COOL: "Pure Cool Series (TP04/TP07/TP09/TP11/PC1)",
    DEVICE_TYPE_PURIFIER_COOL_K: "Purifier Cool K Series (Deprecated - use Pure Cool)",
    DEVICE_TYPE_PURIFIER_COOL_E: "Purifier Cool E Series (Deprecated - use Pure Cool)",
    DEVICE_TYPE_PURIFIER_COOL_M: "Purifier Cool M Series (Deprecated - use Pure Cool)",
    DEVICE_TYPE_PURE_COOL_DESK: "Pure Cool Link Desk",
    DEVICE_TYPE_PURE_COOL_LINK: "Pure Cool Link",
    DEVICE_TYPE_PURE_COOL_LINK_DESK: "Pure Cool Link Desk",
    DEVICE_TYPE_PURE_HOT_COOL: "Pure Hot+Cool Series (HP04/HP07/HP09)",
    DEVICE_TYPE_PURIFIER_HOT_COOL_E: "Pure Hot+Cool E Series (Deprecated - use Pure Hot+Cool)",
    DEVICE_TYPE_PURE_HOT_COOL_LINK: "Pure Hot+Cool Link",
    DEVICE_TYPE_PURE_HUMIDIFY_COOL: "Pure Humidify+Cool Series (PH01/PH02/PH03/PH04)",
    DEVICE_TYPE_PURIFIER_HUMIDIFY_COOL_K: "Purifier Humidify+Cool K Series (Deprecated - use Pure Humidify+Cool)",
    DEVICE_TYPE_PURIFIER_HUMIDIFY_COOL_E: "Purifier Humidify+Cool E Series (Deprecated - use Pure Humidify+Cool)",
    DEVICE_TYPE_PURIFIER_HOT_COOL_K: "Purifier Hot+Cool K Series (Deprecated - use Pure Hot+Cool)",
    DEVICE_TYPE_PURIFIER_BIG_QUIET: "Purifier Big+Quiet Series"
}

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
    MACHINE_OFF = "MACHINE_OFF"


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
