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
        hass.data = {DOMAIN: {DATA_DEVICES: {}, DATA_COORDINATORS: {}}}
        hass.async_create_task = AsyncMock()

        # Mock async_add_executor_job to return a device when called with progressive discovery
        async def mock_executor_job(func, *args, **kwargs):
            if (
                hasattr(func, "__name__")
                and func.__name__ == "get_device_with_progressive_discovery"
            ):
                # Extract serial and device_type from kwargs for clarity and robustness
                serial = kwargs.get("serial")
                device_type = kwargs.get("device_type")

                # Return a mock device for progressive discovery calls
                device = Mock()
                device.serial = serial
                device.device_type = device_type
                device.name = "Test Dyson Device"
                device.version = "1.0.0"
                device.battery_level = 85
                device.is_connected = False
                device.connect = Mock()
                device.disconnect = Mock()
                device.add_message_listener = Mock()
                device.remove_message_listener = Mock()
                device._callbacks = []
                return device
            return True  # Default return for other functions

        hass.async_add_executor_job = AsyncMock(side_effect=mock_executor_job)

        hass.config_entries = Mock()
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
        hass.bus = Mock()
        hass.bus.async_listen_once = Mock()
        hass.loop = Mock()  # Add loop for platform setup
        return hass

    @pytest.fixture
    def mock_config_entry(self):
        """Create a mock config entry."""
        from custom_components.dyson_local.const import (
            CONF_CREDENTIAL,
            CONF_DEVICE_TYPE,
            CONF_SERIAL,
        )

        entry = Mock(spec=ConfigEntry)
        entry.entry_id = "test_entry_id"
        entry.data = {
            CONF_HOST: "192.168.1.100",
            CONF_NAME: "Test Dyson Device",
            CONF_SERIAL: "ABC-DEF-123",
            CONF_CREDENTIAL: "test_credential",
            CONF_DEVICE_TYPE: "520",
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
        device.battery_level = 85  # For DysonBatterySensor tests
        device.is_connected = False  # For connection checks
        device.connect = Mock()  # Connect doesn't return a value
        device.disconnect = Mock()  # Disconnect is called via executor, not async
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
                    "custom_components.dyson_local.connection.DysonConnectionHandler.connect_with_static_host",
                    return_value=True,
                ) as mock_connect:
                    # Mock the connection to store device data as expected
                    def store_device_data(*args, **kwargs):
                        mock_hass.data[DOMAIN][DATA_DEVICES][
                            mock_config_entry.entry_id
                        ] = mock_device
                        return True

                    mock_connect.side_effect = store_device_data

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
        from custom_components.dyson_local.vendor.libdyson.exceptions import (
            DysonException,
        )
        from homeassistant.exceptions import ConfigEntryNotReady

        mock_device.connect = Mock(side_effect=DysonException("Connection failed"))

        # For this test, we need the executor to actually run so the exception is raised
        async def execute_for_failure(func, *args, **kwargs):
            return func(*args, **kwargs)

        mock_hass.async_add_executor_job = execute_for_failure

        with patch(
            "custom_components.dyson_local.vendor.libdyson.get_device_with_progressive_discovery",
            return_value=mock_device,
        ):
            with patch(
                "custom_components.dyson_local.discovery_manager.DysonDiscoveryManager"
            ):
                # Don't mock the connection handler, let it fail naturally
                with pytest.raises(ConfigEntryNotReady):
                    await async_setup_entry(mock_hass, mock_config_entry)

    @pytest.mark.asyncio
    async def test_async_unload_entry_success(
        self, mock_hass, mock_config_entry, mock_device
    ):
        """Test successful unloading of config entry."""
        # Setup initial state - need to add DATA_COORDINATORS too
        from custom_components.dyson_local.const import DATA_COORDINATORS

        mock_hass.data[DOMAIN][DATA_DEVICES] = {mock_config_entry.entry_id: mock_device}
        mock_hass.data[DOMAIN][DATA_COORDINATORS] = {mock_config_entry.entry_id: Mock()}

        with patch(
            "custom_components.dyson_local.discovery_manager.DysonDiscoveryManager"
        ):
            result = await async_unload_entry(mock_hass, mock_config_entry)

            assert result is True
            # Check that async_add_executor_job was called with device.disconnect
            mock_hass.async_add_executor_job.assert_called()
            # The disconnect method should have been called via executor
            calls = mock_hass.async_add_executor_job.call_args_list
            assert any(call[0][0] == mock_device.disconnect for call in calls)

    def test_device_registry_integration(self, mock_device):
        """Test device registry information."""
        from custom_components.dyson_local.entity import DysonEntity

        # Ensure the mock device name is properly accessible
        mock_device.configure_mock(name="Test Dyson Device")

        entity = DysonEntity(mock_device, "Test Entity")
        device_info = entity.device_info

        # Verify device registry integration
        assert device_info["identifiers"] == {(DOMAIN, mock_device.serial)}
        assert device_info["name"] == "Test Entity"  # Entity name, not device name
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
        # Entity IDs are None until added to hass, so just check unique_id
        assert fan_entity.unique_id is not None
        assert sensor_entity.unique_id is not None

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
