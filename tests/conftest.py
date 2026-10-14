"""Home Assistant fixtures."""

import pytest

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def snapshot():
    return {
        "displays": [{"id": "display-1", "name": "Lobby", "playerKey": "must-stay-private"}],
        "display-groups": [{"id": "group-1", "name": "All displays"}],
        "channels": [{"id": "channel-1", "name": "Welcome"}, {"id": "channel-2", "name": "Welcome"}],
        "slides": [{"id": "slide-1", "name": "Hello"}],
        "presets": [{"id": "preset-1", "name": "Welcome preset", "type": "channel"}],
        "assignments": [],
        "alert": None,
    }
