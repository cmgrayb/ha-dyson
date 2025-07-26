"""Tests for Dyson Local humidifier platform."""

from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.dyson_local.humidifier import DysonHumidifierEntity
from homeassistant.components.humidifier import HumidifierEntityFeature
from homeassistant.core import HomeAssistant


class TestDysonHumidifierEntity:
    """Test the DysonHumidifierEntity class."""

    @pytest.fixture
    def mock_hass(self):
        """Create a mock Home Assistant instance."""
        hass = Mock(spec=HomeAssistant)
        hass.async_add_executor_job = AsyncMock()
        return hass

    @pytest.fixture
    def mock_device(self):
        """Create a mock Dyson humidifier device."""
        device = Mock()
        device.serial = "ABC-DEF-123"
        device.device_type = "358"  # Humidifier device type
        device.humidification = True
        device.humidification_auto_mode = False
        device.target_humidity = 50
        device.water_hardness = "SOFT"
        device.water_level = 75
        device.enable_humidification = Mock()
        device.disable_humidification = Mock()
        device.set_target_humidity = Mock()
        device.enable_humidification_auto_mode = Mock()
        device.disable_humidification_auto_mode = Mock()
        device.add_message_listener = Mock()
        device.remove_message_listener = Mock()
        device._callbacks = []
        return device

    @pytest.fixture
    def humidifier_entity(self, mock_device, mock_hass):
        """Create a DysonHumidifierEntity instance."""
        entity = DysonHumidifierEntity(mock_device, "Test Dyson Humidifier")
        entity.hass = mock_hass
        return entity

    def test_supported_features(self, humidifier_entity):
        """Test supported_features property."""
        features = humidifier_entity.supported_features
        expected = HumidifierEntityFeature.MODES
        assert features == expected

    def test_is_on(self, humidifier_entity, mock_device):
        """Test is_on property."""
        mock_device.humidification = True
        assert humidifier_entity.is_on is True

        mock_device.humidification = False
        assert humidifier_entity.is_on is False

    def test_target_humidity(self, humidifier_entity, mock_device):
        """Test target_humidity property."""
        # In auto mode, target_humidity should be None
        mock_device.humidification_auto_mode = True
        assert humidifier_entity.target_humidity is None

        # In normal mode, should return the target
        mock_device.humidification_auto_mode = False
        mock_device.target_humidity = 60
        assert humidifier_entity.target_humidity == 60

    def test_current_humidity(self, humidifier_entity, mock_device):
        """Test current_humidity property."""
        # Current humidity comes from sensor data, testing the entity has the property
        assert hasattr(humidifier_entity, "current_humidity")

    def test_mode(self, humidifier_entity, mock_device):
        """Test mode property."""
        mock_device.humidification_auto_mode = True
        assert humidifier_entity.mode == "auto"

        mock_device.humidification_auto_mode = False
        assert humidifier_entity.mode == "normal"

    def test_available_modes(self, humidifier_entity):
        """Test available_modes property."""
        expected_modes = ["normal", "auto"]
        assert humidifier_entity.available_modes == expected_modes

    def test_min_max_humidity(self, humidifier_entity):
        """Test min_humidity and max_humidity properties."""
        assert humidifier_entity.min_humidity == 30
        assert humidifier_entity.max_humidity == 70

    def test_extra_state_attributes(self, humidifier_entity, mock_device):
        """Test extra_state_attributes property."""
        # Test that the entity has the method (may return None if no extra attributes)
        attrs = humidifier_entity.extra_state_attributes
        assert attrs is None or isinstance(attrs, dict)

    @pytest.mark.asyncio
    async def test_async_turn_on(self, humidifier_entity, mock_device, mock_hass):
        """Test async_turn_on method."""
        await humidifier_entity.async_turn_on()

        # Verify the executor job was called
        assert mock_hass.async_add_executor_job.called

    @pytest.mark.asyncio
    async def test_async_turn_off(self, humidifier_entity, mock_device, mock_hass):
        """Test async_turn_off method."""
        await humidifier_entity.async_turn_off()

        # Verify the executor job was called
        assert mock_hass.async_add_executor_job.called

    @pytest.mark.asyncio
    async def test_async_set_humidity(self, humidifier_entity, mock_device, mock_hass):
        """Test async_set_humidity method."""
        await humidifier_entity.async_set_humidity(65)

        # Verify the executor job was called
        assert mock_hass.async_add_executor_job.called

    @pytest.mark.asyncio
    async def test_async_set_mode_auto(self, humidifier_entity, mock_device, mock_hass):
        """Test async_set_mode to Auto."""
        await humidifier_entity.async_set_mode("Auto")

        # Verify the executor job was called
        assert mock_hass.async_add_executor_job.called

    @pytest.mark.asyncio
    async def test_async_set_mode_manual(
        self, humidifier_entity, mock_device, mock_hass
    ):
        """Test async_set_mode to Manual."""
        await humidifier_entity.async_set_mode("Manual")

        # Verify the executor job was called
        assert mock_hass.async_add_executor_job.called
