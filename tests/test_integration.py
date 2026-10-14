"""Use Home Assistant itself to set up and operate the integration."""

from copy import deepcopy
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_URL
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kiosky.api import KioskyAuthError, KioskyError
from custom_components.kiosky.const import DOMAIN
from custom_components.kiosky.select import SCHEDULE

DATA = {CONF_NAME: "Test Kiosky", CONF_URL: "https://kiosky.test/api/v1", CONF_API_KEY: "secret-token"}


@pytest.fixture
def client(snapshot):
    with patch("custom_components.kiosky.KioskyClient", autospec=True) as factory:
        factory.return_value.snapshot = AsyncMock(return_value=snapshot)
        factory.return_value.request = AsyncMock(return_value={"ok": True})
        yield factory.return_value


async def setup(hass):
    entry = MockConfigEntry(domain=DOMAIN, data=DATA, title="Test Kiosky", unique_id=DATA[CONF_URL])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_setup_entities_select_and_preset(hass, client):
    entry = await setup(hass)
    assert entry.state is ConfigEntryState.LOADED
    states = hass.states.async_all()
    selects = [state for state in states if state.domain == "select"]
    assert len(selects) == 2
    display = next(state for state in selects if state.entity_id.startswith("select.lobby"))
    assert display.state == SCHEDULE
    assert len(display.attributes["options"]) == 3  # Duplicate channel names stay distinct.
    await hass.services.async_call(
        "select", "select_option", {"entity_id": display.entity_id, "option": "Welcome [channel-1]"}, blocking=True
    )
    client.request.assert_awaited_with(
        "POST",
        "assignments",
        {
            "target": {"type": "display", "id": "display-1"},
            "content": {"type": "channel", "id": "channel-1"},
            "priority": 100,
        },
    )
    await hass.services.async_call(
        "select", "select_option", {"entity_id": display.entity_id, "option": SCHEDULE}, blocking=True
    )
    client.request.assert_awaited_with(
        "POST", "presets/stop", {"targets": [{"type": "display", "id": "display-1"}], "endWarnings": False}
    )
    preset = next(state for state in states if state.domain == "button")
    await hass.services.async_call("button", "press", {"entity_id": preset.entity_id}, blocking=True)
    client.request.assert_awaited_with("POST", "presets/preset-1/execute", {})
    assert "must-stay-private" not in str([state.as_dict() for state in hass.states.async_all()])
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert all(state.state == "unavailable" for state in hass.states.async_all())


async def test_actions_and_multiple_installations(hass, client):
    entry = await setup(hass)
    await hass.services.async_call(
        DOMAIN,
        "assign_content",
        {
            "target_type": "group",
            "target_id": "group-1",
            "content_type": "slide",
            "content_id": "slide-1",
            "priority": 500,
            "expires_at": "2026-12-01T23:00:00Z",
        },
        blocking=True,
    )
    client.request.assert_awaited_with(
        "POST",
        "assignments",
        {
            "target": {"type": "group", "id": "group-1"},
            "content": {"type": "slide", "id": "slide-1"},
            "priority": 500,
            "expiresAt": "2026-12-01T23:00:00Z",
        },
    )
    await hass.services.async_call(
        DOMAIN,
        "activate_emergency",
        {
            "targets": [{"type": "group", "id": "group-1"}],
            "warning_type": "information",
            "title": "Test",
            "instructions": "Test message",
        },
        blocking=True,
    )
    client.request.assert_awaited_with(
        "POST",
        "emergencies",
        {
            "targets": [{"type": "group", "id": "group-1"}],
            "warningType": "information",
            "title": "Test",
            "instructions": "Test message",
        },
    )
    await hass.services.async_call(DOMAIN, "end_emergency", {}, blocking=True)
    client.request.assert_awaited_with("DELETE", "emergencies/active", None)
    await hass.services.async_call(
        DOMAIN, "execute_preset", {"preset_id": "preset-1", "end_emergency": False}, blocking=True
    )
    client.request.assert_awaited_with("POST", "presets/preset-1/execute", {"endEmergency": False})
    second = MockConfigEntry(domain=DOMAIN, data={**DATA, CONF_URL: "https://second.test/api/v1"}, title="Second")
    second.add_to_hass(hass)
    assert await hass.config_entries.async_setup(second.entry_id)
    await hass.async_block_till_done()
    with pytest.raises(ServiceValidationError, match="Select one"):
        await hass.services.async_call(DOMAIN, "end_emergency", {}, blocking=True)
    await hass.services.async_call(DOMAIN, "end_emergency", {"config_entry_id": entry.entry_id}, blocking=True)


async def test_refresh_discovers_new_resources(hass, client, snapshot):
    entry = await setup(hass)
    data = deepcopy(snapshot)
    data["displays"].append({"id": "new", "name": "New screen"})
    data["alert"] = {"id": "alert", "type": "information", "title": "Hello", "targets": ["global"]}
    client.snapshot.return_value = data
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert len([state for state in hass.states.async_all() if state.domain == "select"]) == 3
    alert = next(state for state in hass.states.async_all() if state.domain == "binary_sensor")
    assert alert.state == "on"
    assert alert.attributes["title"] == "Hello"


@pytest.mark.parametrize(
    "error,state", [(KioskyAuthError(), ConfigEntryState.SETUP_ERROR), (KioskyError(), ConfigEntryState.SETUP_RETRY)]
)
async def test_setup_failures(hass, client, error, state):
    client.snapshot.side_effect = error
    entry = MockConfigEntry(domain=DOMAIN, data=DATA, title="Test")
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is state


async def test_config_flow(hass):
    with patch("custom_components.kiosky.config_flow.KioskyClient.validate", new_callable=AsyncMock):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        assert result["type"] == "form"
        result = await hass.config_entries.flow.async_configure(result["flow_id"], DATA)
    assert result["type"] == "create_entry"
    assert result["data"] == DATA


@pytest.mark.parametrize("error,reason", [(KioskyAuthError(), "invalid_auth"), (KioskyError(), "cannot_connect")])
async def test_flow_errors(hass, error, reason):
    with patch("custom_components.kiosky.config_flow.KioskyClient.validate", side_effect=error):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], DATA)
        assert result["errors"] == {"base": reason}


async def test_options_and_reauth(hass, client):
    entry = await setup(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"scan_interval": 60})
    assert result["type"] == "create_entry"
    await hass.async_block_till_done()
    assert entry.runtime_data.update_interval.total_seconds() == 60
    with patch("custom_components.kiosky.config_flow.KioskyClient.validate", new_callable=AsyncMock):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "reauth", "entry_id": entry.entry_id}, data=entry.data
        )
        assert result["step_id"] == "reauth_confirm"
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_API_KEY: "new-secret"})
        assert result["reason"] == "reauth_successful"
    await hass.async_block_till_done()
    assert entry.data[CONF_API_KEY] == "new-secret"


async def test_duplicate_and_invalid_url(hass, client):
    await setup(hass)
    with patch("custom_components.kiosky.config_flow.KioskyClient.validate", new_callable=AsyncMock):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], DATA)
        assert result["reason"] == "already_configured"
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**DATA, CONF_URL: "https://user:secret@host/"}
        )
        assert result["errors"] == {"base": "invalid_url"}


async def test_actions_when_unloaded(hass, client):
    entry = await setup(hass)
    assert await hass.config_entries.async_unload(entry.entry_id)
    with pytest.raises(ServiceValidationError, match="not loaded"):
        await hass.services.async_call(DOMAIN, "end_emergency", {}, blocking=True)
