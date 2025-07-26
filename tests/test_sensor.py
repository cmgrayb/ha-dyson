"""Tests for Dyson Local sensor platform."""

from unittest.mock import Mock

import pytest

from custom_components.dyson_local.sensor import (
    DysonBatterySensor,
    DysonFilterLifeSensor,
)


class TestDysonSensors:
    """Test Dyson sensor entities."""

    @pytest.fixture
    def mock_device(self):
        """Create a mock Dyson device."""
        device = Mock()
        device.serial = "ABC-DEF-123"
        device.device_type = "438"
        device.battery_level = 85
        device.hepa_filter_life = 75
        device.carbon_filter_life = 60
        device.add_message_listener = Mock()
        device.remove_message_listener = Mock()
        device._callbacks = []
        return device

    @pytest.fixture
    def battery_sensor(self, mock_device):
        """Create a battery sensor."""
        return DysonBatterySensor(mock_device, "Test Device")

    @pytest.fixture
    def filter_sensor(self, mock_device):
        """Create a filter life sensor."""
        return DysonFilterLifeSensor(mock_device, "Test Device")

    def test_battery_sensor(self, battery_sensor, mock_device):
        """Test battery sensor properties."""
        assert battery_sensor.name == "Test Device Battery Level"
        assert battery_sensor.unique_id == "ABC-DEF-123-battery_level"
        assert hasattr(battery_sensor, "native_value")

    def test_filter_sensor(self, filter_sensor, mock_device):
        """Test filter life sensor properties."""
        assert filter_sensor.name == "Test Device Filter Life"
        assert filter_sensor.unique_id == "ABC-DEF-123-filter_life"
        assert hasattr(filter_sensor, "native_value")
