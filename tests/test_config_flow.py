"""Tests for Dyson Local config flow."""

from unittest.mock import Mock, patch

import pytest

from custom_components.dyson_local.config_flow import DysonLocalConfigFlow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType


class TestDysonLocalConfigFlow:
    """Test the Dyson Local config flow."""

    @pytest.fixture
    def mock_hass(self):
        """Create a mock Home Assistant instance."""
        hass = Mock(spec=HomeAssistant)
        hass.config_entries = Mock()
        hass.config_entries.async_entries.return_value = []
        return hass

    @pytest.fixture
    def config_flow(self, mock_hass):
        """Create a config flow instance."""
        flow = DysonLocalConfigFlow()
        flow.hass = mock_hass
        return flow

    @pytest.mark.asyncio
    async def test_user_form(self, config_flow):
        """Test the user form is shown."""
        result = await config_flow.async_step_user()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        # The result has errors = None, which is fine
        assert result.get("errors") is None or result.get("errors") == {}

    @pytest.mark.asyncio
    async def test_user_form_wifi_method(self, config_flow):
        """Test user form with wifi method."""
        user_input = {"method": "wifi"}

        with patch.object(config_flow, "async_step_wifi") as mock_wifi:
            mock_wifi.return_value = {"type": FlowResultType.FORM}
            await config_flow.async_step_user(user_input)
            mock_wifi.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_form_cloud_method(self, config_flow):
        """Test user form with cloud method."""
        user_input = {"method": "cloud"}

        with patch.object(config_flow, "async_step_cloud") as mock_cloud:
            mock_cloud.return_value = {"type": FlowResultType.FORM}
            await config_flow.async_step_user(user_input)
            mock_cloud.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_form_manual_method(self, config_flow):
        """Test user form with manual method."""
        user_input = {"method": "manual"}

        with patch.object(config_flow, "async_step_manual") as mock_manual:
            mock_manual.return_value = {"type": FlowResultType.FORM}
            await config_flow.async_step_user(user_input)
            mock_manual.assert_called_once()
