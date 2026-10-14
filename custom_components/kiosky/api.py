"""Asynchronous client for the Kiosky External Control API."""

import asyncio
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import aiohttp


class KioskyError(Exception):
    """A connection, protocol, or API error."""


class KioskyAuthError(KioskyError):
    """The API key is invalid or revoked."""


def normalize_url(value: str) -> str:
    """Require the exact API base URL; never accept credentials in URLs."""
    parts = urlsplit(value.strip())
    if (
        parts.scheme not in ("http", "https")
        or not parts.hostname
        or parts.username
        or parts.password
        or parts.fragment
    ):
        raise ValueError("Enter an HTTP(S) API URL without credentials or fragments")
    # WordPress without pretty permalinks uses ?rest_route=/kiosky/v1/control.
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    if query and (set(query) != {"rest_route"} or not query["rest_route"].rstrip("/").endswith("/kiosky/v1/control")):
        raise ValueError("Unsupported API URL query")
    return urlunsplit(
        (parts.scheme, parts.netloc, (parts.path if query else parts.path.rstrip("/")), urlencode(query), "")
    )


class KioskyClient:
    """Use Home Assistant's shared HTTP session without exposing its API key."""

    def __init__(self, session: aiohttp.ClientSession, base_url: str, api_key: str) -> None:
        self.session = session
        self.base_url = normalize_url(base_url)
        self._api_key = api_key.strip()

    def _url(self, path: str) -> str:
        parts = urlsplit(self.base_url)
        query = dict(parse_qsl(parts.query))
        if "rest_route" in query:
            query["rest_route"] = query["rest_route"].rstrip("/") + ("/" + path if path else "")
            return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))
        return self.base_url + ("/" + path if path else "")

    async def request(self, method: str, path: str = "", data: dict | None = None) -> dict[str, Any]:
        """Make one bounded request. Never retry a write or follow redirects."""
        try:
            async with self.session.request(
                method,
                self._url(path),
                json=data,
                headers={"Authorization": f"Bearer {self._api_key}", "Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=15),
                allow_redirects=False,
            ) as response:
                if response.status in (401, 403):
                    raise KioskyAuthError("Kiosky rejected the API key")
                if not 200 <= response.status < 300:
                    # Do not reflect server response bodies or URLs into logs.
                    raise KioskyError(f"Kiosky returned HTTP {response.status}")
                payload = await response.json()
                if not isinstance(payload, dict):
                    raise KioskyError("Kiosky returned an invalid JSON object")
                return payload
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
            raise KioskyError("Cannot communicate with the Kiosky API") from err

    async def validate(self) -> None:
        descriptor = await self.request("GET")
        if descriptor.get("name") != "Kiosky External Control API":
            raise KioskyError("This URL is not a Kiosky External Control API")
        await self.request("GET", "displays")

    async def snapshot(self) -> dict[str, Any]:
        """Fetch coherent resource lists and currently active external assignments."""
        paths = ("displays", "display-groups", "channels", "slides", "presets", "presets/status", "emergencies/active")
        responses = await asyncio.gather(*(self.request("GET", path) for path in paths))
        result = {}
        for path, payload in zip(paths[:5], responses[:5], strict=True):
            if not isinstance(payload.get("data"), list):
                raise KioskyError("Kiosky returned an invalid resource list")
            result[path] = payload["data"]
        assignments = responses[5].get("activeAssignments")
        if not isinstance(assignments, list):
            raise KioskyError("Kiosky returned an invalid assignment list")
        result["assignments"] = assignments
        result["alert"] = responses[6].get("alert")
        return result
