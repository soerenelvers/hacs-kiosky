"""Shared Kiosky entity and device information."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class KioskyEntity(CoordinatorEntity):
    """An entity belonging to a Kiosky server or one of its resources."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, resource_type="server", resource=None):
        super().__init__(coordinator)
        entry = coordinator.config_entry
        resource = resource or {"id": "server", "name": entry.title}
        identifier = f"{entry.entry_id}:{resource_type}:{resource['id']}"
        self._attr_unique_id = identifier
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            name=resource.get("name", resource["id"]),
            manufacturer="Kiosky",
            model={"display": "Display", "group": "Display group", "preset": "Preset", "server": "Server"}[
                resource_type
            ],
        )
        if resource_type != "server":
            self._attr_device_info["via_device"] = (DOMAIN, f"{entry.entry_id}:server:server")
