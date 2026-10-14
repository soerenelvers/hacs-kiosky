"""Validated automation actions for the external API."""

from urllib.parse import quote

from homeassistant.core import callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, TARGET_TYPES, WARNING_TYPES
from .schema import vol

TARGET = vol.Schema({vol.Required("type"): vol.In(TARGET_TYPES), vol.Required("id"): cv.string})
TARGETS = vol.All([TARGET], vol.Length(min=1, max=500))
BASE = {vol.Optional("config_entry_id"): cv.string}
TIMING = {vol.Optional("starts_at"): cv.string, vol.Optional("expires_at"): cv.string}

SCHEMAS = {
    "assign_content": vol.Schema(
        {
            **BASE,
            **TIMING,
            vol.Required("target_type"): vol.In(TARGET_TYPES),
            vol.Required("target_id"): cv.string,
            vol.Required("content_type"): vol.In(("channel", "slide")),
            vol.Required("content_id"): cv.string,
            vol.Optional("priority", default=100): vol.All(vol.Coerce(int), vol.Range(min=0, max=1000)),
        }
    ),
    "clear_assignments": vol.Schema({**BASE, vol.Required("targets"): TARGETS}),
    "execute_preset": vol.Schema(
        {
            **BASE,
            **TIMING,
            vol.Required("preset_id"): cv.string,
            vol.Optional("targets"): TARGETS,
            vol.Optional("channel_id"): cv.string,
            vol.Optional("warning_type"): vol.In(WARNING_TYPES),
            vol.Optional("title"): cv.string,
            vol.Optional("instructions"): cv.string,
            vol.Optional("end_emergency"): cv.boolean,
        }
    ),
    "activate_emergency": vol.Schema(
        {
            **BASE,
            vol.Required("targets"): TARGETS,
            vol.Required("warning_type"): vol.In(WARNING_TYPES),
            vol.Required("title"): vol.All(cv.string, vol.Length(min=1, max=300)),
            vol.Required("instructions"): vol.All(cv.string, vol.Length(min=1, max=3000)),
        }
    ),
    "end_emergency": vol.Schema(BASE),
    "refresh": vol.Schema(BASE),
}


def coordinator_for(hass, entry_id):
    entries = [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if getattr(entry, "runtime_data", None) is not None and entry.state.value == "loaded"
    ]
    if entry_id:
        entries = [entry for entry in entries if entry.entry_id == entry_id]
    if len(entries) != 1:
        raise ServiceValidationError(
            "Select one loaded Kiosky config_entry_id" if entries else "Kiosky installation is not loaded"
        )
    return entries[0].runtime_data


def command_for(service, data):
    """Translate Home Assistant field names into the Kiosky API contract."""
    timing = {api: data[ha] for ha, api in (("starts_at", "startsAt"), ("expires_at", "expiresAt")) if ha in data}
    if service == "assign_content":
        return (
            "POST",
            "assignments",
            {
                "target": {"type": data["target_type"], "id": data["target_id"]},
                "content": {"type": data["content_type"], "id": data["content_id"]},
                "priority": data["priority"],
                **timing,
            },
        )
    if service == "clear_assignments":
        return "POST", "presets/stop", {"targets": data["targets"], "endWarnings": False}
    if service == "execute_preset":
        fields = {
            "targets": "targets",
            "channel_id": "channelId",
            "warning_type": "warningType",
            "title": "title",
            "instructions": "instructions",
            "end_emergency": "endEmergency",
        }
        return (
            "POST",
            f"presets/{quote(data['preset_id'], safe='')}/execute",
            {**{api: data[ha] for ha, api in fields.items() if ha in data}, **timing},
        )
    if service == "activate_emergency":
        return (
            "POST",
            "emergencies",
            {
                "targets": data["targets"],
                "warningType": data["warning_type"],
                "title": data["title"],
                "instructions": data["instructions"],
            },
        )
    return "DELETE", "emergencies/active", None


@callback
def async_register_services(hass):
    async def handle(call):
        coordinator = coordinator_for(hass, call.data.get("config_entry_id"))
        if call.service == "refresh":
            await coordinator.async_refresh()
        else:
            await coordinator.command(*command_for(call.service, call.data))

    for name, schema in SCHEMAS.items():
        hass.services.async_register(DOMAIN, name, handle, schema=schema)
