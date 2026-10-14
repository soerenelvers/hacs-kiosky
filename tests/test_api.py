"""Exercise real HTTP framing, URL handling, and errors."""

import aiohttp
import pytest
from aiohttp import web

from custom_components.kiosky.api import KioskyAuthError, KioskyClient, KioskyError, normalize_url


@pytest.mark.parametrize(
    "value",
    [
        "ftp://host/api/v1",
        "https://user:secret@host/api/v1",
        "https://host/api/v1#secret",
        "https://host/?token=secret",
        "garbage",
    ],
)
def test_invalid_url(value):
    with pytest.raises(ValueError):
        normalize_url(value)


@pytest.mark.parametrize(
    "base,path,expected",
    [
        ("https://host/api/v1/", "displays", "https://host/api/v1/displays"),
        (
            "https://host/sub/wp-json/kiosky/v1/control",
            "assignments",
            "https://host/sub/wp-json/kiosky/v1/control/assignments",
        ),
        ("https://host/sub/kiosky-api/v1", "emergencies/active", "https://host/sub/kiosky-api/v1/emergencies/active"),
        (
            "https://host/sub/?rest_route=/kiosky/v1/control",
            "displays",
            "https://host/sub/?rest_route=%2Fkiosky%2Fv1%2Fcontrol%2Fdisplays",
        ),
    ],
)
def test_platform_urls(base, path, expected):
    assert KioskyClient(None, base, "secret")._url(path) == expected


async def test_http_roundtrip(aiohttp_server, socket_enabled):
    seen = []

    async def handle(request):
        seen.append((request.method, request.path, request.headers.get("Authorization")))
        if request.path.endswith("/bad"):
            return web.json_response({"secret": "do-not-log"}, status=401)
        if request.path.endswith("/redirect"):
            raise web.HTTPFound("/api/v1")
        if request.method == "POST":
            return web.json_response({"received": await request.json()})
        return web.json_response({"name": "Kiosky External Control API"} if request.path == "/api/v1" else {"data": []})

    app = web.Application()
    app.router.add_route("*", "/{path:.*}", handle)
    server = await aiohttp_server(app)
    async with aiohttp.ClientSession() as session:
        client = KioskyClient(session, str(server.make_url("/api/v1")), "test-key")
        await client.validate()
        assert (await client.request("POST", "assignments", {"priority": 200}))["received"] == {"priority": 200}
        with pytest.raises(KioskyAuthError, match="rejected"):
            await client.request("GET", "bad")
        with pytest.raises(KioskyError, match="302"):
            await client.request("GET", "redirect")
    assert all(header == "Bearer test-key" for _, _, header in seen)
    assert len(seen) == 5  # Redirect was not followed.
