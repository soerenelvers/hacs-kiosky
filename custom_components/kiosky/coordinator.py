"""Share API polling across all entities."""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KioskyAuthError, KioskyClient, KioskyError
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class KioskyCoordinator(DataUpdateCoordinator):
    """Poll Kiosky and refresh after successful commands."""

    def __init__(self, hass, entry: ConfigEntry, client: KioskyClient):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
        )
        self.client = client

    async def _async_update_data(self):
        try:
            return await self.client.snapshot()
        except KioskyAuthError as err:
            raise ConfigEntryAuthFailed("Kiosky API key is invalid or revoked") from err
        except KioskyError as err:
            raise UpdateFailed(str(err)) from err

    async def command(self, method: str, path: str, data: dict | None = None):
        try:
            result = await self.client.request(method, path, data)
        except KioskyAuthError as err:
            self.config_entry.async_start_reauth(self.hass)
            raise HomeAssistantError("Kiosky API key is invalid or revoked") from err
        except KioskyError as err:
            raise HomeAssistantError(str(err)) from err
        await self.async_refresh()
        return result
