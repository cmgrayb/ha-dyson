"""Tests for Dyson Local entity base classes."""

from unittest.mock import Mock

import pytest

from custom_components.dyson_local.const import DOMAIN
from custom_components.dyson_local.entity import DysonEntity


class TestDysonEntity:
    """Test the DysonEntity base class."""

    @pytest.fixture
    def mock_device(self):
        """Create a mock Dyson device."""
        device = Mock()
        device.serial = "ABC-DEF-123"
        device.device_type = "438"
        device.add_message_listener = Mock()
        device.remove_message_listener = Mock()
        device._callbacks = []
        # Explicitly delete 'name' attribute so getattr() falls back to entity name
        del device.name
        return device

    @pytest.fixture
    def dyson_entity(self, mock_device):
        """Create a DysonEntity instance."""
        return DysonEntity(mock_device, "Test Dyson Device")

    def test_device_info(self, dyson_entity, mock_device):
        """Test device_info property."""
        device_info = dyson_entity.device_info

        assert device_info.get("identifiers") == {(DOMAIN, "ABC-DEF-123")}
        assert device_info.get("name") == "Test Dyson Device"
        assert device_info.get("manufacturer") == "Dyson"
        assert device_info.get("model") == "438"

    def test_unique_id(self, dyson_entity):
        """Test unique_id property."""
        assert dyson_entity.unique_id == "ABC-DEF-123"

    def test_name(self, dyson_entity):
        """Test name property."""
        assert dyson_entity.name == "Test Dyson Device"

    @pytest.mark.asyncio
    async def test_async_added_to_hass(self, dyson_entity, mock_device):
        """Test async_added_to_hass method."""
        await dyson_entity.async_added_to_hass()

        mock_device.add_message_listener.assert_called_once_with(
            dyson_entity._on_message
        )

    @pytest.mark.asyncio
    async def test_async_will_remove_from_hass(self, dyson_entity, mock_device):
        """Test async_will_remove_from_hass method."""
        await dyson_entity.async_will_remove_from_hass()

        mock_device.remove_message_listener.assert_called_once_with(
            dyson_entity._on_message
        )
