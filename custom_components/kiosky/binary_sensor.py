"""Observe the active Kiosky warning."""

from homeassistant.components.binary_sensor import BinarySensorEntity

from .entity import KioskyEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([KioskyEmergencySensor(entry.runtime_data)])


class KioskyEmergencySensor(KioskyEntity, BinarySensorEntity):
    _attr_name = "Warning active"
    _attr_icon = "mdi:alert"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id += ":emergency"

    @property
    def is_on(self):
        return self.coordinator.data.get("alert") is not None

    @property
    def extra_state_attributes(self):
        alert = self.coordinator.data.get("alert") or {}
        return {key: alert[key] for key in ("id", "type", "title", "targets") if key in alert}
