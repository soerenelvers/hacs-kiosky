"""Kiosky integration for Home Assistant."""

from homeassistant.const import CONF_API_KEY, CONF_URL, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import KioskyClient
from .coordinator import KioskyCoordinator
from .services import async_register_services

PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SELECT, Platform.SENSOR]


async def async_setup(hass, config):
    async_register_services(hass)
    return True


async def async_setup_entry(hass, entry):
    coordinator = KioskyCoordinator(
        hass, entry, KioskyClient(async_get_clientsession(hass), entry.data[CONF_URL], entry.data[CONF_API_KEY])
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_reload_entry(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
