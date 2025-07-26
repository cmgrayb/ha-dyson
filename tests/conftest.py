"""Test configuration for Dyson Local integration."""

from unittest.mock import Mock

import pytest

from custom_components.dyson_local.const import DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component


@pytest.fixture
def mock_config_entry():
    """Return a mock config entry."""
    entry = Mock(spec=ConfigEntry)
    entry.version = 1
    entry.minor_version = 1
    entry.domain = DOMAIN
    entry.title = "Test Dyson Device"
    entry.data = {
        CONF_HOST: "192.168.1.100",
        CONF_NAME: "Test Dyson Device",
        "serial": "ABC-DEF-123",
        "credential": "test_credential",
        "device_type": "438",
    }
    entry.source = "user"
    entry.entry_id = "test_entry_id"
    entry.unique_id = "ABC-DEF-123"
    entry.options = {}
    return entry


@pytest.fixture
async def dyson_integration(hass: HomeAssistant, mock_config_entry):
    """Set up the Dyson integration in Home Assistant."""
    mock_config_entry.add_to_hass(hass)
    await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()
    return mock_config_entry


@pytest.fixture
def mock_dyson_device():
    """Create a mock Dyson device for testing."""

    class MockDysonDevice:
        def __init__(self):
            self.serial = "ABC-DEF-123"
            self.name = "Test Dyson Device"
            self.device_type = "438"
            self.is_connected = True

        def connect(self, host):
            """Mock connect method."""
            self.is_connected = True
            return True

        def disconnect(self):
            """Mock disconnect method."""
            self.is_connected = False

    return MockDysonDevice()
