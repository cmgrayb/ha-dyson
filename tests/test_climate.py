"""Tests for Dyson Local climate platform."""

from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.dyson_local.climate import DysonClimateEntity
from homeassistant.components.climate import ClimateEntityFeature, HVACAction, HVACMode
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant


class TestDysonClimateEntity:
    """Test the DysonClimateEntity class."""

    @pytest.fixture
    def mock_hass(self):
        """Create a mock Home Assistant instance."""
        hass = Mock(spec=HomeAssistant)
        hass.async_add_executor_job = AsyncMock()
        return hass

    @pytest.fixture
    def mock_device(self):
        """Create a mock Dyson device with heating capabilities."""
        device = Mock()
        device.serial = "ABC-DEF-123"
        device.device_type = "527"  # Hot+Cool device type
        device.is_on = True
        device.heat_mode_is_on = True
        device.heat_target = 295  # 22°C in Kelvin
        device.heat_status_is_on = True
        device.auto_mode = False
        device.turn_on = Mock()
        device.turn_off = Mock()
        device.set_heat_target = Mock()
        device.enable_heat_mode = Mock()
        device.disable_heat_mode = Mock()
        device.add_message_listener = Mock()
        device.remove_message_listener = Mock()
        device._callbacks = []
        return device

    @pytest.fixture
    def climate_entity(self, mock_device, mock_hass):
        """Create a DysonClimateEntity instance."""
        entity = DysonClimateEntity(mock_device, "Test Dyson Climate")
        entity.hass = mock_hass
        return entity

    def test_supported_features(self, climate_entity):
        """Test supported_features property."""
        features = climate_entity.supported_features
        expected = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )
        assert features == expected

    def test_temperature_unit(self, climate_entity):
        """Test temperature_unit property."""
        assert climate_entity.temperature_unit == UnitOfTemperature.CELSIUS

    def test_hvac_modes(self, climate_entity):
        """Test hvac_modes property."""
        expected_modes = [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT]
        assert set(climate_entity.hvac_modes) == set(expected_modes)

    def test_hvac_mode(self, climate_entity, mock_device):
        """Test hvac_mode property."""
        # Device is on and in heat mode
        mock_device.is_on = True
        mock_device.heat_mode_is_on = True
        assert climate_entity.hvac_mode == HVACMode.HEAT

        # Device is on but not in heat mode (cooling)
        mock_device.heat_mode_is_on = False
        assert climate_entity.hvac_mode == HVACMode.COOL

        # Device is off
        mock_device.is_on = False
        assert climate_entity.hvac_mode == HVACMode.OFF

    def test_hvac_action(self, climate_entity, mock_device):
        """Test hvac_action property."""
        # Heating
        mock_device.is_on = True
        mock_device.heat_mode_is_on = True
        mock_device.heat_status_is_on = True
        assert climate_entity.hvac_action == HVACAction.HEATING

        # Heat mode but not actively heating
        mock_device.heat_status_is_on = False
        assert climate_entity.hvac_action == HVACAction.IDLE

        # Cooling mode
        mock_device.heat_mode_is_on = False
        assert climate_entity.hvac_action == HVACAction.COOLING

        # Off
        mock_device.is_on = False
        assert climate_entity.hvac_action == HVACAction.OFF

    def test_target_temperature(self, climate_entity, mock_device):
        """Test target_temperature property."""
        # Temperature is stored in Kelvin, converted to Celsius (22°C = 295K)
        mock_device.heat_target = 295
        assert climate_entity.target_temperature == 22

    def test_min_max_temp(self, climate_entity):
        """Test min_temp and max_temp properties."""
        assert climate_entity.min_temp == 1
        assert climate_entity.max_temp == 37

    @pytest.mark.asyncio
    async def test_async_set_hvac_mode_heat(
        self, climate_entity, mock_device, mock_hass
    ):
        """Test async_set_hvac_mode to heat."""
        await climate_entity.async_set_hvac_mode(HVACMode.HEAT)

        # Verify executor jobs were called
        assert mock_hass.async_add_executor_job.called

    @pytest.mark.asyncio
    async def test_async_set_hvac_mode_fan_only(
        self, climate_entity, mock_device, mock_hass
    ):
        """Test async_set_hvac_mode to fan only."""
        await climate_entity.async_set_hvac_mode(HVACMode.FAN_ONLY)

        # Verify executor jobs were called
        assert mock_hass.async_add_executor_job.called

    @pytest.mark.asyncio
    async def test_async_set_hvac_mode_off(
        self, climate_entity, mock_device, mock_hass
    ):
        """Test async_set_hvac_mode to off."""
        await climate_entity.async_set_hvac_mode(HVACMode.OFF)

        # Verify executor jobs were called
        assert mock_hass.async_add_executor_job.called

    @pytest.mark.asyncio
    async def test_async_set_temperature(self, climate_entity, mock_device, mock_hass):
        """Test async_set_temperature method."""
        await climate_entity.async_set_temperature(temperature=25)

        # Verify the executor job was called
        assert mock_hass.async_add_executor_job.called
