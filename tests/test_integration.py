"""Integration tests for Dyson Local component."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from custom_components.dyson_local import async_setup_entry, async_unload_entry
from custom_components.dyson_local.const import DATA_COORDINATORS, DATA_DEVICES, DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant


class TestDysonLocalIntegration:
    """Test integration scenarios for Dyson Local component."""

    @pytest.fixture
    def mock_hass(self):
        """Create a mock Home Assistant instance."""
        hass = Mock(spec=HomeAssistant)
        hass.data = {
            DOMAIN: {
                DATA_DEVICES: {},
                DATA_COORDINATORS: {},
                "discovery_count": 0,
                "device_ips": {},
            }
        }
        hass.async_create_task = AsyncMock()

        # Mock async_add_executor_job to actually execute the function
        async def mock_executor_job(func, *args, **kwargs):
            """Mock executor that runs the function directly."""
            return func(*args, **kwargs)

        hass.async_add_executor_job = AsyncMock(side_effect=mock_executor_job)
        hass.bus = Mock()
        hass.bus.async_listen_once = Mock()
        # Add config_entries mock for unload tests
        hass.config_entries = Mock()
        hass.config_entries.async_forward_entry_unload = AsyncMock(return_value=True)
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
        hass.loop = Mock()  # Mock the event loop
        return hass

    @pytest.fixture
    def mock_config_entry(self):
        """Create a mock config entry."""
        entry = Mock(spec=ConfigEntry)
        entry.entry_id = "test_entry_id"
        entry.data = {
            CONF_HOST: "192.168.1.100",
            CONF_NAME: "Test Dyson Device",
            "serial": "ABC-DEF-123",
            "credential": "test_credential",
            "device_type": "520",
        }
        entry.options = {}
        return entry

    @pytest.fixture
    def mock_device(self):
        """Create a mock Dyson device."""
        device = Mock()
        device.serial = "ABC-DEF-123"
        device.device_type = "520"  # Generic device type
        device.name = "Test Dyson Device"
        device.version = "1.0.0"
        device.connect = Mock(return_value=True)  # Make this synchronous, not async
        device.disconnect = Mock()
        device.add_message_listener = Mock()
        device.remove_message_listener = Mock()
        device._callbacks = []
        return device

    @pytest.mark.asyncio
    async def test_async_setup_entry_success(
        self, mock_hass, mock_config_entry, mock_device
    ):
        """Test successful setup of config entry."""
        with patch(
            "custom_components.dyson_local.device_manager.get_device",
            return_value=mock_device,
        ):
            with patch(
                "custom_components.dyson_local.discovery_manager.DysonDiscoveryManager"
            ):
                with patch(
                    "custom_components.dyson_local.connection.DysonConnectionHandler._setup_platforms",
                    return_value=True,
                ):
                    result = await async_setup_entry(mock_hass, mock_config_entry)

                    assert result is True
                    assert DATA_DEVICES in mock_hass.data[DOMAIN]
                    assert (
                        mock_config_entry.entry_id
                        in mock_hass.data[DOMAIN][DATA_DEVICES]
                    )

    @pytest.mark.asyncio
    async def test_async_setup_entry_connection_failed(
        self, mock_hass, mock_config_entry, mock_device
    ):
        """Test setup failure when device connection fails."""
        # Mock the device.connect to raise an exception to simulate connection failure
        from libdyson.exceptions import DysonException

        mock_device.connect = Mock(side_effect=DysonException("Connection failed"))

        with patch(
            "custom_components.dyson_local.device_manager.get_device",
            return_value=mock_device,
        ):
            # This should raise ConfigEntryNotReady, which means the setup failed as expected
            from homeassistant.exceptions import ConfigEntryNotReady

            with pytest.raises(ConfigEntryNotReady):
                await async_setup_entry(mock_hass, mock_config_entry)

    @pytest.mark.asyncio
    async def test_async_unload_entry_success(
        self, mock_hass, mock_config_entry, mock_device
    ):
        """Test successful unloading of config entry."""
        # Setup initial state with proper data structure
        mock_hass.data[DOMAIN][DATA_DEVICES] = {mock_config_entry.entry_id: mock_device}
        mock_hass.data[DOMAIN][DATA_COORDINATORS] = {mock_config_entry.entry_id: None}

        with patch(
            "custom_components.dyson_local.discovery_manager.DysonDiscoveryManager"
        ):
            result = await async_unload_entry(mock_hass, mock_config_entry)

            assert result is True
            # Device should be disconnected via the async_add_executor_job
            mock_hass.async_add_executor_job.assert_called()

    def test_device_registry_integration(self, mock_device):
        """Test device registry information."""
        from custom_components.dyson_local.entity import DysonEntity

        entity = DysonEntity(mock_device, "Test Entity")
        device_info = entity.device_info

        # Verify device registry integration
        assert device_info["identifiers"] == {(DOMAIN, mock_device.serial)}
        assert device_info["name"] == mock_device.name
        assert device_info["manufacturer"] == "Dyson"
        assert device_info["model"] == mock_device.device_type

    def test_entity_unique_id_generation(self, mock_device):
        """Test unique ID generation across different entity types."""
        from custom_components.dyson_local.entity import DysonEntity

        class TestSubEntity(DysonEntity):
            @property
            def sub_unique_id(self):
                return "test_sensor"

        entity = TestSubEntity(mock_device, "Test Entity")
        expected_unique_id = f"{mock_device.serial}-test_sensor"
        assert entity.unique_id == expected_unique_id

    @pytest.mark.asyncio
    async def test_callback_management(self, mock_device):
        """Test that entities properly manage device callbacks."""
        from custom_components.dyson_local.entity import DysonEntity

        entity = DysonEntity(mock_device, "Test Entity")

        # Simulate adding to hass
        entity._device._callbacks = []
        await entity.async_added_to_hass()

        # Verify callback was added
        mock_device.add_message_listener.assert_called()

        # Simulate removal from hass
        await entity.async_will_remove_from_hass()

        # Verify callback was removed
        mock_device.remove_message_listener.assert_called()

    def test_platform_coexistence(self, mock_device):
        """Test that multiple platform entities can coexist."""
        from custom_components.dyson_local.fan import DysonFanEntity
        from custom_components.dyson_local.sensor import DysonBatterySensor

        # Create entities from different platforms
        fan_entity = DysonFanEntity(mock_device, "Test Fan")
        sensor_entity = DysonBatterySensor(mock_device, "Test Sensor")

        # Both should have unique identifiers
        assert fan_entity.unique_id != sensor_entity.unique_id
        # Note: entity_id is None until added to hass, so we skip that comparison

        # Both should reference the same device
        assert fan_entity._device == sensor_entity._device

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, mock_device):
        """Test error handling in entity methods."""
        from custom_components.dyson_local.fan import DysonFanEntity

        entity = DysonFanEntity(mock_device, "Test Fan")
        entity.hass = Mock()
        entity.hass.async_add_executor_job = AsyncMock()

        # Test that async methods handle device errors gracefully
        mock_device.turn_on.side_effect = Exception("Device error")

        # Should not raise exception
        await entity.async_turn_on()

        # Should still call the executor job
        assert entity.hass.async_add_executor_job.called
