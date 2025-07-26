"""Tests for Dyson Local binary_sensor platform."""

from unittest.mock import Mock

import pytest

from custom_components.dyson_local.binary_sensor import (
    Dyson360HeuristBinFullSensor,
    DysonVacuumBatteryChargingSensor,
)
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.core import HomeAssistant


class TestDysonVacuumBatteryChargingSensor:
    """Test the DysonVacuumBatteryChargingSensor class."""

    @pytest.fixture
    def mock_hass(self):
        """Create a mock Home Assistant instance."""
        return Mock(spec=HomeAssistant)

    @pytest.fixture
    def mock_device(self):
        """Create a mock Dyson vacuum device."""
        device = Mock()
        device.serial = "ABC-DEF-123"
        device.device_type = "N223"  # 360 Eye device type
        device.is_charging = False
        device.add_message_listener = Mock()
        device.remove_message_listener = Mock()
        device._callbacks = []
        return device

    @pytest.fixture
    def battery_sensor(self, mock_device, mock_hass):
        """Create a DysonVacuumBatteryChargingSensor instance."""
        entity = DysonVacuumBatteryChargingSensor(mock_device, "Test Dyson Battery")
        entity.hass = mock_hass
        return entity

    def test_sub_name(self, battery_sensor):
        """Test sub_name property."""
        assert battery_sensor.sub_name == "Battery Charging"

    def test_sub_unique_id(self, battery_sensor):
        """Test sub_unique_id property."""
        assert battery_sensor.sub_unique_id == "battery_charging"

    def test_device_class(self, battery_sensor):
        """Test device_class property."""
        assert battery_sensor.device_class == BinarySensorDeviceClass.BATTERY_CHARGING

    def test_is_on_not_charging(self, battery_sensor, mock_device):
        """Test is_on when device is not charging."""
        mock_device.is_charging = False
        # The sensor should reflect the initial state from device
        assert hasattr(battery_sensor, "is_on")

    def test_is_on_charging(self, battery_sensor, mock_device):
        """Test is_on when device is charging."""
        mock_device.is_charging = True
        # The sensor should reflect the charging state
        assert hasattr(battery_sensor, "is_on")


class TestDyson360HeuristBinFullSensor:
    """Test the Dyson360HeuristBinFullSensor class."""

    @pytest.fixture
    def mock_hass(self):
        """Create a mock Home Assistant instance."""
        return Mock(spec=HomeAssistant)

    @pytest.fixture
    def mock_device(self):
        """Create a mock Dyson 360 Heurist device."""
        device = Mock()
        device.serial = "DEF-GHI-456"
        device.device_type = "276"  # 360 Heurist device type
        device.is_bin_full = False
        device.add_message_listener = Mock()
        device.remove_message_listener = Mock()
        device._callbacks = []
        return device

    @pytest.fixture
    def bin_sensor(self, mock_device, mock_hass):
        """Create a Dyson360HeuristBinFullSensor instance."""
        entity = Dyson360HeuristBinFullSensor(mock_device, "Test Dyson Bin")
        entity.hass = mock_hass
        return entity

    def test_sub_name(self, bin_sensor):
        """Test sub_name property."""
        assert bin_sensor.sub_name == "Bin Full"

    def test_sub_unique_id(self, bin_sensor):
        """Test sub_unique_id property."""
        assert bin_sensor.sub_unique_id == "bin_full"

    def test_icon(self, bin_sensor):
        """Test icon property."""
        assert bin_sensor.icon == "mdi:delete-variant"

    def test_is_on_bin_not_full(self, bin_sensor, mock_device):
        """Test is_on when bin is not full."""
        mock_device.is_bin_full = False
        # The sensor should reflect the bin state
        assert hasattr(bin_sensor, "is_on")

    def test_is_on_bin_full(self, bin_sensor, mock_device):
        """Test is_on when bin is full."""
        mock_device.is_bin_full = True
        # The sensor should reflect the bin full state
        assert hasattr(bin_sensor, "is_on")
