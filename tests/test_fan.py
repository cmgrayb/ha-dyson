"""Tests for Dyson Local fan platform."""

from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.dyson_local.fan import DysonFanEntity, DysonPureCoolEntity
from homeassistant.components.fan import FanEntityFeature
from homeassistant.core import HomeAssistant


class TestDysonFanEntity:
    """Test the DysonFanEntity class."""

    @pytest.fixture
    def mock_hass(self):
        """Create a mock Home Assistant instance."""
        hass = Mock(spec=HomeAssistant)
        hass.async_add_executor_job = AsyncMock()
        return hass

    @pytest.fixture
    def mock_device(self):
        """Create a mock Dyson device."""
        device = Mock()
        device.serial = "ABC-DEF-123"
        device.device_type = "438"
        device.is_on = True
        device.auto_mode = False
        device.speed = 5
        device.oscillation = False
        device.night_mode = False
        device.carbon_filter_life = 50
        device.hepa_filter_life = 75
        device.turn_on = Mock()
        device.turn_off = Mock()
        device.set_speed = Mock()
        device.enable_oscillation = Mock()
        device.disable_oscillation = Mock()
        device.enable_auto_mode = Mock()
        device.disable_auto_mode = Mock()
        device.reset_filter = Mock()
        device.add_message_listener = Mock()
        device.remove_message_listener = Mock()
        device._callbacks = []
        # Add oscillation angle attributes for extra_state_attributes
        device.oscillation_angle_low = 5
        device.oscillation_angle_high = 355
        return device

    @pytest.fixture
    def fan_entity(self, mock_device, mock_hass):
        """Create a DysonFanEntity instance."""
        entity = DysonFanEntity(mock_device, "Test Dyson Device")
        entity.hass = mock_hass
        return entity

    def test_supported_features(self, fan_entity):
        """Test supported_features property."""
        features = fan_entity.supported_features
        expected = (
            FanEntityFeature.OSCILLATE
            | FanEntityFeature.SET_SPEED
            | FanEntityFeature.PRESET_MODE
            | FanEntityFeature.TURN_OFF
            | FanEntityFeature.TURN_ON
        )
        assert features == expected

    def test_is_on(self, fan_entity, mock_device):
        """Test is_on property."""
        mock_device.is_on = True
        assert fan_entity.is_on is True

        mock_device.is_on = False
        assert fan_entity.is_on is False

    def test_oscillating(self, fan_entity, mock_device):
        """Test oscillating property."""
        mock_device.oscillation = True
        assert fan_entity.oscillating is True

        mock_device.oscillation = False
        assert fan_entity.oscillating is False

    def test_percentage(self, fan_entity, mock_device):
        """Test percentage property."""
        mock_device.speed = 5
        mock_device.auto_mode = False
        # Speed 5 out of 10 = 50%
        expected = int((5 / 10) * 100)
        assert fan_entity.percentage == expected

        mock_device.auto_mode = True
        assert fan_entity.percentage is None

    def test_speed_count(self, fan_entity):
        """Test speed_count property."""
        assert fan_entity.speed_count == 10

    def test_preset_modes(self, fan_entity):
        """Test preset_modes property."""
        assert "Auto" in fan_entity.preset_modes

    def test_preset_mode(self, fan_entity, mock_device):
        """Test preset_mode property."""
        mock_device.auto_mode = True
        assert fan_entity.preset_mode == "Auto"

        mock_device.auto_mode = False
        assert fan_entity.preset_mode == "Normal"

    @pytest.mark.asyncio
    async def test_async_turn_on(self, fan_entity, mock_device, mock_hass):
        """Test async_turn_on method."""
        await fan_entity.async_turn_on(percentage=60)

        # Verify the executor job was called
        assert mock_hass.async_add_executor_job.called

    @pytest.mark.asyncio
    async def test_async_turn_off(self, fan_entity, mock_device, mock_hass):
        """Test async_turn_off method."""
        await fan_entity.async_turn_off()

        # Verify the executor job was called
        assert mock_hass.async_add_executor_job.called

    @pytest.mark.asyncio
    async def test_async_set_percentage(self, fan_entity, mock_device, mock_hass):
        """Test async_set_percentage method."""
        await fan_entity.async_set_percentage(80)

        # Verify the executor job was called
        assert mock_hass.async_add_executor_job.called

    @pytest.mark.asyncio
    async def test_async_oscillate(self, fan_entity, mock_device, mock_hass):
        """Test async_oscillate method."""
        await fan_entity.async_oscillate(True)

        # Verify the executor job was called
        assert mock_hass.async_add_executor_job.called

    @pytest.mark.asyncio
    async def test_async_set_preset_mode(self, fan_entity, mock_device, mock_hass):
        """Test async_set_preset_mode method."""
        await fan_entity.async_set_preset_mode("Auto")

        # Verify the executor job was called
        assert mock_hass.async_add_executor_job.called

    def test_extra_state_attributes(self, fan_entity, mock_device):
        """Test extra_state_attributes property for base fan entity."""
        # Base DysonFanEntity doesn't have extra_state_attributes
        # The method exists in the parent Entity class and may return None or {}
        attrs = fan_entity.extra_state_attributes

        # The base entity might not have extra attributes, so this is acceptable
        assert attrs is None or isinstance(attrs, dict)


class TestDysonPureCoolEntity:
    """Test the DysonPureCoolEntity class with angle support."""

    @pytest.fixture
    def mock_hass(self):
        """Create a mock Home Assistant instance."""
        hass = Mock(spec=HomeAssistant)
        hass.async_add_executor_job = AsyncMock()
        return hass

    @pytest.fixture
    def mock_device(self):
        """Create a mock Dyson device with oscillation support."""
        device = Mock()
        device.serial = "ABC-DEF-123"
        device.device_type = "438"
        device.oscillation_angle_low = 5
        device.oscillation_angle_high = 355
        device.oscillation = False
        device.front_airflow = True
        device.add_message_listener = Mock()
        device.remove_message_listener = Mock()
        device._callbacks = []
        return device

    @pytest.fixture
    def cool_entity(self, mock_device, mock_hass):
        """Create a DysonPureCoolEntity instance."""
        entity = DysonPureCoolEntity(mock_device, "Test Dyson Pure Cool")
        entity.hass = mock_hass
        return entity

    def test_angle_properties(self, cool_entity, mock_device):
        """Test angle_low and angle_high properties."""
        assert cool_entity.angle_low == 5
        assert cool_entity.angle_high == 355

    def test_extra_state_attributes_with_angles(self, cool_entity, mock_device):
        """Test extra_state_attributes property with angle support."""
        attrs = cool_entity.extra_state_attributes

        assert attrs is not None
        assert isinstance(attrs, dict)
        assert "angle_low" in attrs
        assert "angle_high" in attrs
        assert attrs["angle_low"] == 5
        assert attrs["angle_high"] == 355
