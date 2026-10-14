"""Optional end-to-end test with the actual proprietary Kiosky server.

KIOSKY_TEST_SERVER_REPO=/path/to/Kiosky KIOSKY_TEST_NODE=/path/to/node pytest -q tests/test_live_kiosky.py
The public CI suite uses HTTP fixtures and the real Home Assistant runtime.
"""

import asyncio
import os
import secrets
import shutil
import socket
import subprocess
from pathlib import Path

import aiohttp
import pytest
from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_URL
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kiosky.const import DOMAIN

pytestmark = pytest.mark.skipif(
    not os.environ.get("KIOSKY_TEST_SERVER_REPO"), reason="Optional live Kiosky server test"
)


async def test_real_player_control(hass, socket_enabled, tmp_path):
    repo = Path(os.environ["KIOSKY_TEST_SERVER_REPO"])
    node = os.environ.get("KIOSKY_TEST_NODE") or shutil.which("node")
    assert node and (repo / "dist/server/index.js").is_file()
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    admin_key = secrets.token_hex(32)
    env = {
        **os.environ,
        "KIOSKY_HOST": "127.0.0.1",
        "KIOSKY_PORT": str(port),
        "KIOSKY_DATABASE_PATH": str(tmp_path / "test.sqlite"),
        "KIOSKY_ADMIN_API_KEY": admin_key,
        "KIOSKY_ENCRYPTION_KEY": secrets.token_hex(32),
        "KIOSKY_UPDATE_AUTO_CHECK": "false",
        "KIOSKY_GEOCODING_ENABLED": "false",
    }
    log = (tmp_path / "server.log").open("w")
    process = subprocess.Popen([node, str(repo / "dist/server/index.js")], cwd=repo, env=env, stdout=log, stderr=log)
    base = f"http://127.0.0.1:{port}"
    try:
        async with aiohttp.ClientSession() as session:
            for _ in range(200):
                try:
                    async with session.get(base + "/api/health") as response:
                        if response.status == 200:
                            break
                except aiohttp.ClientError:
                    pass
                await asyncio.sleep(0.05)
            else:
                pytest.fail("Kiosky server did not start")

            async def request(method, path, data=None, headers=None):
                async with session.request(
                    method, base + path, json=data, headers=headers or {"X-API-Key": admin_key}
                ) as response:
                    value = await response.json()
                    assert response.status < 400, value
                    return value

            key = (await request("POST", "/api/api-users", {"name": "HA integration test"}))["token"]
            slide = (
                await request(
                    "POST",
                    "/api/slides",
                    {
                        "name": "HA Slide",
                        "type": "custom",
                        "orientation": "landscape",
                        "status": "ready",
                        "document": {"elements": []},
                    },
                )
            )["slide"]
            channel = (
                await request(
                    "POST",
                    "/api/channels",
                    {
                        "name": "HA Channel",
                        "orientation": "landscape",
                        "status": "ready",
                        "items": [{"slideId": slide["id"], "durationSeconds": 12, "transition": "inherit"}],
                    },
                )
            )["channel"]
            display = (
                await request(
                    "POST",
                    "/api/displays",
                    {
                        "name": "HA Screen",
                        "slug": "ha-test",
                        "orientation": "landscape",
                        "defaultChannelId": channel["id"],
                        "timezone": "Europe/Berlin",
                        "status": "active",
                        "groupIds": [],
                    },
                )
            )["display"]
            entry = MockConfigEntry(
                domain=DOMAIN,
                title="Live Kiosky",
                unique_id=base,
                data={CONF_NAME: "Live Kiosky", CONF_URL: base + "/api/v1", CONF_API_KEY: key},
            )
            entry.add_to_hass(hass)
            assert await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()
            await hass.services.async_call(
                DOMAIN,
                "assign_content",
                {
                    "target_type": "display",
                    "target_id": display["id"],
                    "content_type": "slide",
                    "content_id": slide["id"],
                },
                blocking=True,
            )
            player = await request("GET", "/api/player/ha-test/state", headers={"X-Player-Key": display["playerKey"]})
            assert player["directSlide"]["id"] == slide["id"]
            await hass.services.async_call(
                DOMAIN,
                "activate_emergency",
                {
                    "warning_type": "information",
                    "title": "HA warning",
                    "instructions": "Live test",
                    "targets": [{"type": "display", "id": display["id"]}],
                },
                blocking=True,
            )
            player = await request("GET", "/api/player/ha-test/state", headers={"X-Player-Key": display["playerKey"]})
            assert player["emergency"]["title"] == "HA warning"
            sensor = next(state for state in hass.states.async_all() if state.domain == "binary_sensor")
            assert sensor.state == "on"
            await hass.services.async_call(
                DOMAIN, "clear_assignments", {"targets": [{"type": "display", "id": display["id"]}]}, blocking=True
            )
            assert (await request("GET", "/api/v1/emergencies/active"))["alert"] is not None
            await hass.services.async_call(DOMAIN, "end_emergency", {}, blocking=True)
            assert (await request("GET", "/api/v1/emergencies/active"))["alert"] is None
            assert await hass.config_entries.async_unload(entry.entry_id)
    finally:
        process.terminate()
        try:
            await asyncio.to_thread(process.wait, timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            await asyncio.to_thread(process.wait)
        log.close()
